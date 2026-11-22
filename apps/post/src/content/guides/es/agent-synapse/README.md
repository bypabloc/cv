# Guardrails para tu agente de código: que no borre, no filtre secretos ni toque lo que no debe

> Guía práctica para instalar y operar Synapse, un plugin de guardrails para Claude Code, Codex, Antigravity y OpenCode: bloquea comandos destructivos, escrituras fuera del proyecto, lecturas de `.env` y secretos antes de que el agente los ejecute, sin pedirte permiso para lo rutinario. Con el caso de estudio de cómo se portó a cuatro agentes y las cifras medidas en semanas de uso.

**Costo:** USD 0 (plugin MIT) · **Tiempo:** ~1 h para instalarlo y leer la guía · **Nivel:** intermedio (hooks, git, Python)

---

## TL;DR

- **El problema:** con los permisos nativos, el agente te interrumpe cada pocos minutos o, si los apagas, puede borrar, filtrar o reescribir algo sin que nadie lo vea.
- **La solución:** cuatro hooks que revisan cada herramienta **antes** de ejecutarla y deciden `allow`, `ask`, `block` o `pass` con reglas deterministas (~8 ms por comando) ([cap. 03](03-que-decide.md)).
- **Qué cubre:** comandos destructivos y fuera del proyecto, escritura de archivos desde Bash, lectura de `.env`, credenciales en lo que se escribe y archivos troncales como `.git/` o los lockfiles.
- **Cuatro agentes, una lógica:** Claude Code, Codex, Antigravity y OpenCode usan el mismo núcleo; cambia solo la entrada y la salida de cada host ([cap. 02](02-instalacion.md) y [cap. 09](09-portar-a-cuatro-agentes.md)).
- **Laya:** un clasificador neuronal opcional para los casos ambiguos. Solo puede pedir confirmación, nunca bloquear, y viene apagado porque la traza real mostró que sus 24 confirmaciones fueron falsos positivos ([cap. 08](08-laya.md)).
- **Traza de cada decisión:** quién decidió, con qué regla y por qué, en un JSONL diario ([cap. 07](07-la-traza.md)).
- **Plugin listo para instalar:** [bypabloc/agent-plugin-synapse](https://github.com/bypabloc/agent-plugin-synapse), espejo del monorepo [bypabloc/agent-plugins](https://github.com/bypabloc/agent-plugins).

---

## De dónde salió la idea

Synapse nació de los bloqueos constantes. Con los permisos por defecto, el agente se detenía cada pocos minutos a pedir confirmación para un `rm` de un archivo de prueba, un `gh pr create` o una lectura de `.git`, y yo tenía que estar pendiente de la pantalla para que el trabajo avanzara. La alternativa, apagar los permisos, era peor: nada impedía un `rm -rf` fuera del proyecto, un `cat .env` volcado en el contexto o un `git push --force`.

Quería lo contrario de las dos cosas: que el agente dejara de depender de que yo lo vigilara y que lo peligroso se detuviera solo. Primero lo armé como hooks sueltos dentro de un proyecto; después los separé en un plugin para usarlo en cualquiera. Con Laya como apoyo para lo ambiguo y con las reglas que aprendí de su traza, hoy le doy al agente mucha más libertad: dejo una corrida autónoma en marcha y me voy a dormir sin preocuparme por lo que pueda tocar.

---

## El caso de estudio

Uso Synapse a diario desde octubre de 2026 en varios proyectos propios: monorepos con worktrees, corridas autónomas de horas y sesiones en paralelo con distintos agentes, en WSL y en Windows. Cada versión del plugin salió de un fallo visto en una sesión real y quedó documentada con su síntoma, su causa, la prueba que lo cubre y la lección.

Los proyectos no se nombran y las rutas son de ejemplo; las cifras son mediciones reales de esas sesiones. Cada capítulo cierra con un bloque **En mi caso** que cuenta qué pasó al aplicarlo.

---

## La familia agent-plugins

Synapse vive en el monorepo [bypabloc/agent-plugins](https://github.com/bypabloc/agent-plugins), que es la fuente de verdad de mis plugins para agentes de código. Cada plugin se publica además en su propio repo espejo y se instala desde el mismo marketplace (`bypabloc-agents`):

| Plugin | Qué hace | Agentes |
| :-- | :-- | :-- |
| [synapse](https://github.com/bypabloc/agent-plugin-synapse) | Los guardrails de esta guía | Claude Code, Codex, Antigravity, OpenCode |
| [session-handoff](https://github.com/bypabloc/agent-plugin-session-handoff) | Guarda el estado del trabajo en disco y lo reinyecta al iniciar y compactar; no deja cerrar el turno con trabajo pendiente. Lo explico en [Que tu agente de código no pierda el foco](https://post.the-full-stack.com/agents-handoff/) | Claude Code, Codex, Antigravity, OpenCode |
| [spanish-latam-style](https://github.com/bypabloc/claude-plugin-spanish-latam) | Español neutro latinoamericano en respuestas, documentación, commits y código | Claude Code (Codex ejecuta sus hooks) |

El tercero salió de un problema concreto. Varias veces, al trabajar en español, el agente me escribía código, docstrings, mensajes de commit y documentación con voseo argentino ("ejecutá", "fijate", "tenés"). No tengo ningún problema con el voseo ni con los argentinos, pero en el código que revisan mis compañeros de trabajo no corresponde: los code reviews llegaban con voseos que nadie del equipo usa. El plugin inyecta una regla de español neutro con tuteo en cada sesión y en cada mensaje, para que no se diluya en sesiones largas, y trae un linter para revisarlo en CI.

---

## Índice

| # | Capítulo | Qué resuelve |
| :-- | :-- | :-- |
| 01 | [Por qué un agente necesita guardrails](01-el-problema.md) | Lo que puede salir mal y por qué los permisos nativos no bastan |
| 02 | [Instalar en cada agente](02-instalacion.md) | Claude Code, Codex, Antigravity y OpenCode, con requisitos |
| 03 | [Qué bloquea, qué pregunta y qué deja pasar](03-que-decide.md) | Los cuatro hooks y las cuatro decisiones |
| 04 | [El alcance del proyecto y los borrados recuperables](04-alcance-del-proyecto.md) | Qué es "dentro del proyecto" y cuándo un borrado no necesita permiso |
| 05 | [Secretos y archivos .env](05-secretos-y-env.md) | Leer `.env` sin volcarlo y no escribir credenciales |
| 06 | [Configurar por proyecto](06-configurar-por-proyecto.md) | Comandos rutinarios, excepciones exactas y variables |
| 07 | [La traza: quién decidió y por qué](07-la-traza.md) | Leer el log y depurar un falso positivo |
| 08 | [Laya: un clasificador que solo puede preguntar](08-laya.md) | Qué es, sus cifras y por qué viene apagado |
| 09 | [Caso de estudio: portar a cuatro agentes](09-portar-a-cuatro-agentes.md) | Núcleo neutral, adaptadores y el golden sin regresiones |
| 10 | [Codex y Windows: lo que costó horas](10-codex-y-windows.md) | El `ask` que detiene al agente y los fallos de Windows |
| 11 | [Probar, actualizar y vigilar](11-probar-y-operar.md) | Tests, casos declarativos, releases y vigilancia |
| 12 | [Problemas, mitos y lo que se midió](12-problemas-y-soluciones.md) | Lo que falló, lo que no hace y el balance |

---

## Convenciones

- **Rutas de ejemplo:** `~/code/mi-app` es un proyecto cualquiera; `<plugin>` es la carpeta donde quedó instalado el plugin.
- **Versiones probadas:** Claude Code 2.1.329 (mínima 2.1.287), Codex 0.171.0 (mínima 0.171), Antigravity CLI `agy` 1.5.13 (mínima 1.5.4), OpenCode 2.3.2 (mínima V2 2.3), Python 3.10 o superior. Synapse 1.7.3.
- **Evidencia de cada dato:** **[doc]** documentación oficial, **[prueba]** ejecutado y observado, **[medido]** con números reales, **[uso real]** visto en semanas de uso, **[criterio]** razonamiento sin medición.
- **Fecha de los datos:** noviembre de 2026.

`claude-code` `codex` `opencode` `antigravity` `seguridad` `hooks` `guardrails`
