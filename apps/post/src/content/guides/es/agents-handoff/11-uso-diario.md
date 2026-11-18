**11**

# Uso diario y varias sesiones

[← Índice](README.md)

---

### Una vez por máquina

- **Claude Code:** instalar el plugin de compactación desde el checkout principal ([cap. 08](08-compactar-sin-resumen.md)), si lo usas.
- **Codex:** instalar el hook de usuario con su guarda por repo, aprobarlo en `/hooks` y reiniciar la sesión ([cap. 05](05-configurar-cada-agente.md)).
- **OpenCode:** `opencode service restart` tras cambiar el plugin o `opencode.json`.

### La rutina

1. **Abre las sesiones en la raíz del checkout principal** y trabaja en worktrees de `../<repo>-worktrees/`.
2. **Vincula la sesión:** escribe el nombre del trabajo en `tmp/handoff/.sessions/<session_id>` con la herramienta de archivos; el hook te da el `session_id` al iniciar.
3. **Mantén las líneas de estado** arriba de `PROGRESS.md`, en inglés y con ≤ 120 caracteres. Actualízalas después de cada commit o decisión y antes de una corrida larga o una pausa.
4. **Esperar no es bloquear:** CI, un merge, un candado o un recurso compartido son `Phase: external-wait`.
5. **Decide y anota** en el registro de decisiones en vez de preguntar, salvo las cuatro categorías de `blocked`.
6. **Tras una pausa larga:** Claude Code y OpenCode siguen solos. En Codex y Antigravity, abre una sesión nueva y escribe «retoma el trabajo `<nombre>`», o reenvía el mensaje si prefieres el contexto completo.
7. **Al compactar:** con el plugin de Claude Code no hay resumen, solo sobreviven el handoff y ~20k tokens recientes. Sin el plugin, `PreCompact` le pide al resumen que conserve el trabajo y el siguiente paso.
8. **Al cerrar el trabajo:** borra su carpeta del handoff y sus vínculos, en el mismo paso que quitas el worktree.
9. **Para revisar qué pasó:** consulta `tmp/handoff/.log/events.jsonl`.

### Que el agente siga trabajando

| Lo que pasaba | Qué lo corrige |
| :-- | :-- |
| Tomaba un aviso de presupuesto de tokens como un límite: compactaba, resumía y cerraba el turno | El mensaje reinyectado ordena seguir con el `Next step` y aclara que esos avisos no son un límite. Un hook `Stop` bloquea el cierre mientras haya `Next step` sin `Status: done\|blocked`, y deja parar tras 3 bloqueos seguidos sin cambios en `PROGRESS.md` (anti-bucle) |
| Marcaba `blocked` por una espera y, al retomar, preguntaba aunque el motivo ya no existía | La espera es `external-wait`, y ahí `Stop` deja parar. Al retomar un `blocked`, comprueba el motivo y, si ya no aplica, sigue sin preguntar |
| Se detenía a preguntar «(a) o (b)» algo que podía decidir | `blocked` exige una categoría: **datos de producción**, **costo**, **credenciales** o **pedido del usuario de parar**. Un `PreToolUse` rechaza la herramienta de preguntas mientras corre un plan. Toda otra decisión se toma eligiendo la opción correcta, no la más rápida, y se anota en un registro versionado con motivo y alternativas |
| Las líneas de estado eran párrafos de ~1500 caracteres y `PROGRESS.md` pesaba 14 KB | Tope de 120 caracteres. El aviso llega **justo después de editar** el archivo (`PostToolUse`): con el aviso solo al reinyectar, la sesión volvía a escribirlas largas |
| Horas esperando un candado cuyo proceso ya había muerto | Antes de esperar o declarar `blocked`, `kill -0 <pid>` del candado: sin archivo o con el PID muerto, está libre |
| Escribió el vínculo con `echo >` y un guardarraíl lo bloqueó | La regla dice que el handoff se escribe con la herramienta de archivos |

### Corridas autónomas

En una corrida autónoma el usuario no escribe por horas, y todo lo que dependía de «el último mensaje del usuario» falló: el plugin abría la cola solo en un mensaje del usuario, y todo era un solo turno, así que el recorte de turnos viejos no recortaba nada ([cap. 08](08-compactar-sin-resumen.md)).

Un recordatorio periódico (cron) despertó la sesión seis veces y cada vez entregó un reporte y se detuvo. **El prompt del recordatorio debe ordenar retomar el trabajo** después del reporte, no solo informar.

### Worktrees fuera del repo

- Con los worktrees en una carpeta **dentro** del repo, una sesión del principal carga las reglas del worktree como reglas anidadas, y la cola conservada las vuelve a adjuntar duplicadas.
- Ponlos en `../<repo>-worktrees/<nombre>/`, declarados en `permissions.additionalDirectories` para leer y editar sin prompts. Los scripts que buscan worktrees o transcripts deben reconocer la ruta nueva.
- **La regla sola no basta:** un handoff anterior al cambio decía la ruta vieja y el agente le hizo caso. Un hook `PreToolUse` de `Bash` que rechace `git worktree add <ruta dentro del repo>` (exit 2 y la ruta sugerida) lo corta. La regla debe decir que manda sobre lo que diga un handoff viejo.
- No abras sesiones dentro de un worktree: el handoff del principal queda fuera del workspace y Claude Code, Codex y Antigravity piden aprobación (en headless la deniegan sin fallar).

### Recursos pesados compartidos: un turno por host

Varias sesiones corriendo E2E contra un stack real, grabaciones de API y benchmarks a la vez saturan la máquina. El protocolo:

1. Antes de una corrida pesada, un comando que lee `/proc` y el registro de sesiones del agente dice quién usa el recurso (exit 0 libre, 1 ocupado), de qué sesión cuelga y qué sesiones del proyecto están abiertas.
2. Libre: avisar «ocupo el recurso» a las demás sesiones y correr.
3. Ocupado: pedirle a la dueña que avise al liberar, programar un chequeo cada ~10 min **solo mientras se espera** y seguir con lo que no lo usa.
4. Al terminar: avisar «libre» y borrar el chequeo.

El estado del turno va en `PROGRESS.md`, y el mensaje reinyectado repite el protocolo: así sobrevive a la compactación.

### Instrucciones cortadas sin aviso

Cada agente tiene un límite de instrucciones y ninguno falla de forma ruidosa:

| Agente | Lo que pasó |
| :-- | :-- |
| Claude Code | Avisó «21 instruction files add up to 150.7k chars, over the 150.0k-char total limit» |
| Codex | Leía `AGENTS.md` (~50 KB) cortado a 32 KiB, el `project_doc_max_bytes` por defecto |
| Antigravity | Descartaba 17 reglas sin frontmatter `trigger`; además hay un límite de ~24 KB por regla |

- Un chequeo en el pre-commit que descubre lo que carga cada agente (repo y home), lo mide contra sus límites y falla nombrando el archivo a recortar.
- Reglas como **núcleo corto + referencia**: lo que se carga siempre queda breve y el detalle va a un documento que se lee cuando hace falta.
- Límites propios: ~15 000 caracteres por archivo y ~80 000 de todo lo que se carga siempre.

### En mi caso

Con los worktrees dentro del repo, al entrar a cada worktree nuevo la llamada siguiente a compactar subió a ~120k y ~131k (frente a ~95k): de +24k a +45k tokens solo por reglas duplicadas. Moverlos afuera y agregar el hook que bloquea `git worktree add` dentro del repo lo resolvió. Con las instrucciones, `AGENTS.md` pasó de 49 KB a 6,5 KB al separar núcleo y referencia.

`worktrees` `sesiones-paralelas` `autonomía` `flujo-de-trabajo`
