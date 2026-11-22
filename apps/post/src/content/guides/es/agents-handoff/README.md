# Que tu agente de código no pierda el foco

> Guía práctica para que Claude Code, Codex, OpenCode y Antigravity sigan un trabajo largo sin perder decisiones ni el paso actual: compactar antes, guardar el estado en disco, reinyectarlo con hooks, retomar tras una pausa sin pagar todo el historial y evitar que el agente corte el trabajo. Con el caso real de mis proyectos y sus cifras medidas.

**Costo:** USD 0 (solo configuración y un script) · **Tiempo:** ~2 h la primera vez · **Nivel:** avanzado (hooks, git worktrees, Python, TypeScript)

---

## TL;DR

- **El problema:** al llenarse el contexto, el agente resume la conversación y el resumen pierde decisiones, el siguiente paso y las trampas ya encontradas. Tras una pausa larga, además, la caché vence y el siguiente mensaje se cobra completo.
- **Compactar antes:** un umbral versionado en el repo. Claude Code al 60 %, Codex al 65 % más un tope en tokens, OpenCode con 40 % de la ventana libre.
- **Handoff en disco:** `tmp/handoff/<trabajo>/` con `PROGRESS.md`, `DECISIONS.md` y `NOTES.md`. Un solo script lo reinyecta en los cuatro agentes después de compactar, al iniciar y al volver de una pausa.
- **Que el agente siga:** un hook de cierre de turno que no deja parar mientras haya un `Next step`; `blocked` solo por cuatro motivos.
- **Compactar sin resumen (Claude Code):** un plugin conserva los ~20k tokens recientes tal cual. Ahorra ~37–64 s por compactación; en tokens queda cerca del empate.
- **Plugin listo para instalar (Claude Code, Codex, Antigravity y OpenCode):** [session-handoff](https://github.com/bypabloc/agent-plugin-session-handoff), del monorepo [agent-plugins](https://github.com/bypabloc/agent-plugins), empaqueta el handoff, el bloqueo de cierre de turno y, en Claude Code, la compactación sin resumen ([cap. 09](09-receta-del-plugin.md)).
- **Varias sesiones:** worktrees fuera del repo, una carpeta por trabajo y un vínculo por sesión.

---

## De dónde salió la idea

Todo empezó con un post que circulaba en redes sociales. Decía que conviene pedirle a Claude, en el `CLAUDE.md`, que empiece cada respuesta con tu nombre: no por simpatía, sino como **canario**. El modelo no pasa de funcionar bien a alucinar de golpe; primero deja de cumplir una instrucción pequeña. Si un día deja de llamarte por tu nombre, el canario murió y es momento de abrir una sesión nueva. El post le atribuía la técnica a Peter Steinberger, el creador de OpenClaw.

Al revisar la fuente, el propio Steinberger lo desmintió [en X](https://x.com/steipete/status/2113741901384089824):

> «No, nunca lo llamé canary y no tengo archivos claude.md.»

La atribución era falsa, pero la observación de fondo me sirvió: la ventana de contexto se degrada de a poco, y para cuando lo notas el agente ya trabaja con un resumen que perdió lo importante. En vez de esperar a que el canario muera, quise que la sesión no dependiera de lo que recuerda la conversación. De ahí salió el handoff en disco: gestionar el conocimiento del trabajo fuera del contexto, reinyectarlo cuando hace falta y compactar antes de que la ventana se sature. La prueba del marcador del [capítulo 10](10-probar-el-handoff.md) es, de hecho, un canario deliberado: un dato que solo puede responder si el handoff llegó.

---

## El caso de estudio

Todo lo que sigue lo armé y lo usé en mis proyectos: un monorepo con varias apps y un backend, donde trabajo con sesiones de varias horas, corridas autónomas que ejecutan un plan tras otro sin que yo escriba nada y hasta cuatro sesiones en paralelo, cada una en su worktree. Probé los cuatro agentes con las versiones de noviembre de 2026 y dejé el sistema corriendo varias semanas antes de escribir esto.

Las rutas y los nombres de trabajos están anonimizados; las cifras son mediciones reales de esas sesiones. Cada capítulo cierra con un bloque **En mi caso** que cuenta qué pasó al aplicarlo.

---

## Índice

| # | Capítulo | Qué resuelve |
| :-- | :-- | :-- |
| 01 | [Por qué el agente pierde el hilo](01-el-problema.md) | Los seis problemas y qué parte de la guía resuelve cada uno |
| 02 | [Compactar antes](02-compactar-antes.md) | El umbral versionado de cada agente y cómo comprobarlo |
| 03 | [El handoff en disco](03-handoff-en-disco.md) | Los tres archivos, las líneas de estado y dónde viven |
| 04 | [El script común de los hooks](04-script-comun.md) | Un script en Python sin dependencias para los cuatro agentes |
| 05 | [Configurar cada agente](05-configurar-cada-agente.md) | Claude Code, Codex, OpenCode y Antigravity, con sus trampas |
| 06 | [Saber cuándo venció la caché](06-cache-de-prompt.md) | TTL, campos de uso y mediciones por agente |
| 07 | [Retomar tras una pausa larga](07-pausa-larga.md) | Seguir con el handoff en vez de reenviar el historial |
| 08 | [Claude Code: compactar sin resumen](08-compactar-sin-resumen.md) | El diseño del plugin y por qué quedó así |
| 09 | [Receta del plugin, paso a paso](09-receta-del-plugin.md) | Código completo, tests e instalación |
| 10 | [Probar que el handoff llega](10-probar-el-handoff.md) | La prueba del marcador y los comandos sin interfaz |
| 11 | [Uso diario y varias sesiones](11-uso-diario.md) | Rutina, estados, decisiones y recursos compartidos |
| 12 | [Problemas, mitos y lo que se midió](12-problemas-y-soluciones.md) | Lo que falló, lo que circula y es falso, y el balance |

---

## Convenciones

- **Rutas de ejemplo:** `<repo>` es el checkout principal (`~/code/mi-app`); `../<repo>-worktrees/` es la carpeta de worktrees, **fuera** del repo; `<plan>` es la carpeta de la especificación del trabajo (`docs/specs/042-login-form/`).
- **Handoff:** `<repo>/tmp/handoff/`, dentro de una carpeta ignorada por git. El script vive en `<repo>/agent-hooks/session_handoff.py` (versionado).
- **Versiones probadas:** Claude Code 2.1.3xx, Codex `codex-cli 0.167.0`, OpenCode `2.0.29` y Antigravity CLI `agy 1.5.3`.
- **Plugin session-handoff 0.5.4:** Claude Code 2.1.287 o posterior, Codex ≥ 0.171, `agy` ≥ 1.5.4 y OpenCode V2 ≥ 2.3 (probado con Codex 0.171.0, `agy` 1.5.13 y OpenCode 2.3.2).
- **Evidencia de cada dato:** **[doc]** documentación oficial, **[bin]** visto en el binario o su caché, **[prueba]** ejecutado y observado, **[medido]** con números reales, **[cálculo]** con tarifas oficiales, **[uso real]** visto en semanas de uso, **[comunidad]** blog o issue sin verificar, **[criterio]** razonamiento sin medición. Al actualizar un agente, vuelve a probar lo marcado **[prueba]** y **[bin]**.
- **Fecha de los datos:** noviembre de 2026.

`claude-code` `codex` `opencode` `antigravity` `context-engineering` `hooks` `prompt-caching`
