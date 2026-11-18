**08**

# Claude Code: compactar sin resumen

[← Índice](README.md)

---

### Por qué

Con el handoff en disco y reinyectado por `SessionStart` `compact`, la compactación igual llama al modelo para resumir toda la conversación (~600k tokens al 60 % de 1M). Esa llamada es lenta, y casi todo lo que produce ya está en el handoff. Los hooks clásicos no la reemplazan: `PreCompact` solo cambia las instrucciones o la bloquea, y `SessionStart` actúa cuando ya terminó.

Este capítulo explica el diseño y por qué quedó así. El código está en el [capítulo 09](09-receta-del-plugin.md).

### La pieza que lo permite: plugins con módulo

Claude Code carga plugins con un módulo TypeScript que corre dentro del proceso y atiende eventos del motor (acceso anticipado: la API puede cambiar). El evento `session.compact` se dispara antes de cada compactación (`/compact`, el umbral, otro plugin o el precálculo):

| Respuesta del hook | Efecto |
| :-- | :-- |
| `next(e)` | Compactación normal: `PreCompact` y el resumen del modelo |
| `next({ ...e, instructions })` o `next({ ...e, messages })` | Cambia las instrucciones o lo que se resume |
| `{ skip: "motivo" }` | No compacta |
| `{ messages }` propio, sin `next` | **La conversación queda con esos mensajes y el resumidor no corre** |

Un mensaje devuelto con su `handle` queda tal cual lo tiene el motor, bloques de herramientas incluidos. Uno sin `handle` se rearma con su `role` y su texto, sin `thinking` ni adjuntos.

### El diseño final

1. **Precálculo** (resumen anticipado): se omite con `skip`; se compacta cuando hace falta, con el estado de ese momento.
2. **Subagente:** `next(e)`, resumen normal.
3. **¿Hay trabajo vinculado?** Si no, `next(e)`.
4. **La cola:** los mensajes más recientes que caben en ~80 000 caracteres (~20k tokens, a ~4 caracteres por token):
   - El corte abre en un mensaje del asistente o en uno del usuario **sin** resultados de herramienta: ningún resultado queda sin su llamada.
   - Los turnos anteriores al último pedido del usuario se devuelven **sin `handle`**: el motor los rearma sin `thinking` ni reglas anidadas.
   - El turno en curso queda entero (la API exige su `thinking` intacto), y cada mensaje entero pesa ×3 en el presupuesto.
   - Si con ese peso no cabe ningún corte seguro, se reintenta sin ponderar; lo mismo si el corte deja menos de 12 mensajes y sin ponderar caben más.
   - Si ni así cabe, `next(e)`.
5. **Respuesta:** un aviso («conversación compactada sin resumen; el handoff llega aparte y manda; si el trabajo no terminó, sigue con el siguiente paso»), un «Understood.» (que se omite si la cola abre en el asistente, para que los roles alternen) y la cola. **No** repite el handoff: `SessionStart` `compact` lo inyecta justo después.
6. **Bitácora:** cada decisión (`kept` con cuántos mensajes, o `fallback` con su motivo) va al registro del handoff.

En el camino del plugin **no corre `PreCompact`** (tampoco los hooks globales que dependan de él, como un respaldo de la transcripción); sí corren `PostCompact` y `SessionStart` `compact`.

### Instalación: marketplace local con scope `project`

En `.claude/settings.json`, versionado:

```json
"enabledPlugins": { "<plugin>@<marketplace>": true },
"extraKnownMarketplaces": { "<marketplace>": { "source": { "source": "directory", "path": "./<carpeta>" } } }
```

Una vez por máquina, **desde el checkout principal**:

```bash
claude plugin marketplace add ./<carpeta> --scope project
claude plugin install <plugin>@<marketplace> --scope project
git checkout .claude/settings.json   # la CLI reordena el archivo y guarda una ruta absoluta
claude plugin list                   # Scope: project · Read from: <repo>/<carpeta>/<plugin>
```

- **La CLI reescribe `settings.json`** con la ruta absoluta: restaura el versionado.
- **No instales desde un worktree:** el registro del usuario guarda esa ruta y se rompe al borrarlo. Arreglo: `uninstall`, `marketplace remove` y repetir desde el principal.
- `install` sin el `marketplace add` previo falla con «not found in marketplace».
- Al editar el plugin, `/reload-plugins` lo relee sin reinstalar.

### Opcional: el estado del trabajo a la vista

El mismo plugin puede leer las líneas de estado (modo `--status` del script) al iniciar, en cada prompt, al cerrar el turno y tras cada `Write` o `Edit`:

- El **spinner** muestra `<Phase> · <Current> · ETA <ETA>` mientras el turno trabaja.
- Una **banda** de una línea sobre el prompt con `● estado · fase · ETA · ctx <n>%`; el motivo solo si está `blocked`. El porcentaje sale del hook `session.measure`. Una banda con párrafos completos ocupaba media pantalla.

### Límites

- Solo Claude Code; los demás agentes siguen con su compactación y su handoff.
- Los plugins no tienen sandbox: este ejecuta `git` y `python3` en el directorio de la sesión.
- Con `--resume`, la cadena de mensajes vuelve a traer los originales con su `thinking`: el recorte rige solo en la sesión en curso.
- Lo que no esté en el handoff ni en la cola se pierde: mantén `PROGRESS.md` al día.

### En mi caso

El diseño final es la séptima versión. Cada fila es un fallo real:

| Versión | Problema | Corrección |
| :-- | :-- | :-- |
| Limitar a los últimos 3 prompts | Los recordatorios de los hooks también son mensajes de usuario con texto | Solo presupuesto de tamaño |
| Repetir el handoff en la respuesta | Llegaba dos veces (`SessionStart` corre igual) | Solo el aviso |
| Cola de ~80k que abría solo en un mensaje del usuario con texto | En corridas autónomas, sin mensajes del usuario por horas, cayó al resumen en 31 de 32 compactaciones | Abrir también en el asistente |
| La misma cola, medida en uso real | Medía mucho más que el tope (p90 316k): ~90 % era `thinking` y reglas anidadas que el estimador no veía | Turnos viejos sin `handle` y tope de ~20k |
| Sin ponderar | En corridas autónomas todo es un turno: nada se recortaba (188 de 188 mensajes) | Peso ×3 para los mensajes enteros |
| Con peso ×3 | Un lote de 14 lecturas en paralelo no cabía y caía al resumen | Reintento sin ponderar |
| Corte ponderado | Una vez dejó 6 de 1006 mensajes y el agente releyó el plan | Mínimo de 12 |

El resultado, medido sobre mis transcripts: el plugin responde en ~90 ms frente a una mediana de 52 s del resumen, y ahorra ~37–64 s por compactación. En tokens **no ahorra**: la llamada asentada siguiente quedó en ~133k frente a ~124k con resumen. Lo mantengo por el tiempo y porque lo reciente queda literal, no parafraseado ([cap. 12](12-problemas-y-soluciones.md)).

`claude-code` `plugin` `compactación` `diseño`
