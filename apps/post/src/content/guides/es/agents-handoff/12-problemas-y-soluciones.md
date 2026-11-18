**12**

# Problemas, mitos y lo que se midió

[← Índice](README.md)

---

### Problemas y soluciones

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| El hook de Codex no corre en un worktree | Los hooks de proyecto solo corren en rutas de confianza aprobadas; cada worktree es otra ruta | Hook **de usuario** con guarda por repo |
| Codex marca el hook como `Failed` | La salida empieza con `[` y la lee como JSON | Emitir JSON (`hookSpecificOutput.additionalContext`) |
| Codex inyecta el handoff dos veces | Hook de usuario más `.codex/hooks.json` en el repo | Solo el de usuario |
| Cambié el hook de Codex y dejó de correr | La confianza se guarda por hash | Reaprobar en `/hooks` y reiniciar |
| `agy` ignora `.agents/hooks.json` | Formato de Claude Code o JSON mal formado; el error solo va al log | Mapa de hooks con nombre; revisar `~/.gemini/antigravity-cli/log/` |
| OpenCode ignora `compaction.buffer` | `"40%"` se descarta en la 2.0.29 | Un entero (`400000`) y `opencode debug config` |
| El plugin de OpenCode no actúa en un worktree | Dos plugins con el mismo `id` | Ruta del checkout en el `id` |
| El plugin de OpenCode no toma los cambios | El servicio en segundo plano conserva el `setup` viejo | `opencode service restart`; probar con `--standalone` |
| El script nuevo no se ejecuta | Los agentes corren la copia del checkout principal, atrasado | Actualizar el principal tras fusionar |
| El plugin de Claude Code se rompió | Se instaló desde un worktree que se borró | `uninstall`, `marketplace remove` y repetir desde el principal |
| El trabajo figura sin siguiente paso | Claves de estado traducidas (`Siguiente paso:`) | Claves en inglés |
| `PROGRESS.md` crece y se trunca | Se usa como bitácora | Estado actual; el historial está en `git log` |
| El agente sigue un handoff viejo | No se actualizó antes de una pausa o una compactación | Reescribirlo tras cada commit y decisión; contrastarlo con git |

### Afirmaciones que resultaron falsas

Después de implementar, contrasté cada afirmación con la documentación oficial y fuentes recientes, y probé cada discrepancia con las versiones instaladas (Claude Code 2.1.319, Codex 0.167.0, OpenCode 2.0.29, agy 1.5.3). Varias circulan en blogs:

| # | Afirmación | Realidad | Evidencia |
| :-- | :-- | :-- | :-- |
| 1 | Codex ignora el texto plano en la salida de `SessionStart` | **Lo inyecta.** Solo falla si la salida empieza con `[` | Texto plano con un marcador: el modelo lo respondió; con `[`: `Failed` |
| 2 | `agy -p` no acepta comandos de barra | **Sí los acepta**; `/compact` creó un `CHECKPOINT` | Prueba y `--disable-slash-commands` en `agy --help` |
| 3 | El `ephemeralMessage` de Antigravity no queda en la trayectoria | **Queda guardado** (y lo usa el resumen), pero **no se reenvía** | +1500 tokens en el turno vinculado y +210 por turno después |
| 4 | `PreCompact` de Claude Code no influye en el resumen | **Su stdout son instrucciones para el resumen**; con exit 2 bloquea | Documentación y un `/compact` real |
| 5 | OpenCode pide confirmación para escribir fuera del proyecto | `external_directory` **lo permite por defecto** | Documentación |
| 6 | El tope del 90 % de Codex rige desde cierta versión | Viene de un PR upstream; la versión no se confirmó | Código upstream |
| 7 | `model_auto_compact_token_limit` actúa a mitad de turno | La documentación no lo dice; viene de un blog | Documentación |

Sin confirmar en la documentación, pero sí en la práctica: el hook `context` de OpenCode, que los subagentes de Claude Code reciben el `session_id` de su padre (solo lo dice una issue) y el log de errores de hooks de `agy`.

### Medir la compactación: las métricas engañan

Una sola prueba con `/compact` mide velocidad, no tokens. Hace falta un script que lea los transcripts del checkout y sus worktrees y separe dos cohortes: compactaciones sin resumen (de menos de 2 s) y con resumen.

| Lección | Detalle |
| :-- | :-- |
| El tamaño post-compactación que reporta el agente engaña | No incluye la base de la sesión ni los adjuntos de la cola. Mide la **entrada de la primera llamada** tras el corte |
| La primera llamada tampoco basta | Entre la primera y la segunda, Claude Code repone sus listados (skills, herramientas diferidas, agentes, MCP: ~20k). Compara la **llamada asentada** |
| Filtrar por fecha de archivo mezcla versiones | Una sesión larga mete sus compactaciones viejas. Filtra cada una por su `timestamp`, en UTC |
| Releer el handoff no es retrabajo | Es lo que pide la regla. Exclúyelo de la métrica |
| Cuenta respuestas, no entradas | Una respuesta registrada en varias entradas con el mismo id es una sola llamada |

### En mi caso: el balance

| Medición | Resultado |
| :-- | :-- |
| 747 compactaciones, primera versión del plugin | Sin resumen: 89 ms de mediana, 69 min ahorrados en 80 compactaciones; retrabajo igual (4,4 % frente a 4,5 %) |
| Cola de ~80k, primera llamada | 197k de mediana frente a 164k del resumen: neto −26,5M tokens equivalentes |
| Cola de ~20k sin `thinking` viejo, 14 compactaciones de una corrida | ~96k de mediana, 0 caídas al resumen, 0 errores de API, retrabajo 0,4 % |
| Llamada asentada (22 sin resumen, 2 con resumen) | ~133k frente a ~124k: neto −3,19M; ahorra ~37–64 s por compactación |

**Conclusión:** compactar sin resumen gana en tiempo y en literalidad de lo reciente; en tokens queda cerca del empate, levemente peor. Antes de cambiar el tope de la cola, mide desde la hora del cambio: el resultado neto no debe empeorar, el retrabajo no debe subir y el ahorro de tiempo debe mantenerse. Como referencia, OpenCode V2 deja 15k tokens literales, y un estudio de JetBrains en SWE-bench muestra que enmascarar resultados viejos de herramientas iguala o supera al resumen con LLM a la mitad del costo.

### Lo que no medí

- **La tasa de alucinaciones antes y después.** Lo que hay son pruebas con marcadores de que la información correcta llega al modelo (tras `/compact`, al reanudar y tras una pausa) y mediciones de la compactación en sesiones reales.
- **La calidad del resumen al 60 % frente al 97 %.**
- El retrabajo medido solo cuenta repeticiones exactas de lecturas o comandos: no ve errores por contexto perdido.

### Riesgos que conviene tener presentes

- **Un handoff desactualizado es peor que no tenerlo:** el agente confía en él.
- **El corte, la sesión nueva y la compactación sin resumen descartan lo que no se escribió en disco.**
- **Fricción:** Codex y Antigravity bloquean una vez el primer mensaje tras la pausa.
- **Secretos:** el handoff entra al contexto del modelo y puede quedar en transcripciones. Nunca tokens, `.env` ni PII.

`troubleshooting` `mediciones` `mitos` `compactación`
