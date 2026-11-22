# Code Mode en Claude Code: cuándo ahorra y cuándo no

> Guía práctica de Code Mode, el modo experimental de Claude Code en el que el modelo escribe JavaScript para encadenar sus herramientas en vez de pedirlas una por una: cómo activarlo, qué cambia, de dónde sale el ahorro, en qué tareas conviene y en cuáles es más lento, qué pasa con los permisos y los hooks, y cómo medirlo en tus propios proyectos. Con mis mediciones en proyectos reales.

**Costo:** USD 0 (viene en Claude Code) · **Tiempo:** ~10 min para activarlo, ~1 h para medirlo bien · **Nivel:** intermedio (terminal, hooks, permisos)

---

## TL;DR

- **Qué es:** con `CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1`, Claude deja de pedir las herramientas de a una y escribe un script que busca, lee, edita y prueba en un solo paso; al modelo solo le vuelve lo que el script devuelve ([cap. 01](01-que-es.md)).
- **Dónde ahorra:** en tareas con muchas llamadas cuyos resultados se pueden reducir a un total, un conteo o una lista corta, sobre todo vía MCP. Ahí el contexto añadido cae a una fracción ([cap. 05](05-cuando-ahorra.md)).
- **Dónde no:** en trabajo con archivos locales que Claude ya resolvía con un `rg` o un script de Python. Puede salir igual o **más lento**, a veces con cientos de lecturas sueltas ([cap. 06](06-cuando-no.md)).
- **Un ahorro fijo:** cada sesión arranca con unos 13 mil tokens menos de definiciones de herramientas ([cap. 04](04-de-donde-sale-el-ahorro.md)).
- **Seguridad:** cada llamada interna pasa por tus reglas y hooks; el clasificador de auto mode, en cambio, revisa el script entero sin ver los valores que se calculan al ejecutarlo ([cap. 09](09-permisos-y-hooks.md)).
- **Requisitos:** terminal interactiva, instalación nativa, cuenta directa de Anthropic y Opus 5.5, Sonnet 5.5, Haiku 5.5 o Fable 5.2. No corre con `claude -p`, VS Code ni Desktop ([cap. 02](02-activar.md)).
- **No te creas un porcentaje único:** mide la misma tarea con el modo encendido y apagado ([cap. 11](11-medirlo.md)).

---

## De dónde salió la idea

Sigo de cerca cada versión de Claude Code, y cuando la 2.1.323 (12 de noviembre de 2026) trajo Code Mode, me llamó la atención de inmediato: la promesa era que el modelo dejara de hacer un viaje por cada herramienta y resolviera en un script lo que antes eran diez turnos. Trabajo con sesiones largas y corridas autónomas, así que cada viaje que se ahorra se nota en tiempo y en cuota.

La promesa venía sin cifras oficiales: Anthropic no publicó cuánto ahorra. Así que, en vez de creerle a los porcentajes que empezaron a circular, lo encendí en mis proyectos y comparé.

---

## El caso de estudio

Llevo unos ocho días usándolo en trabajo real: **klinikae** (una plataforma web con backend y varias apps) y **content-studio** (un estudio de contenido con flujos de video), además de este portfolio y mi monorepo de plugins. Lo usé en WSL y en Windows, sobre todo con Opus 5.5 y algunas sesiones con Haiku 5.5.

Las cifras de mis sesiones salen de los transcripts que guarda Claude Code ([cap. 07](07-mis-mediciones.md)); las pruebas publicadas por otros están aparte, con su fuente ([cap. 08](08-lo-que-midieron-otros.md)). Cada capítulo cierra con un bloque **En mi caso**.

---

## Índice

| # | Capítulo | Qué resuelve |
| :-- | :-- | :-- |
| 01 | [Qué es Code Mode y qué cambia](01-que-es.md) | Del paso a paso al script |
| 02 | [Activarlo y comprobar que está encendido](02-activar.md) | Requisitos, variable, `/status` y `Ctrl+O` |
| 03 | [Cómo se ve un bloque de código](03-anatomia-de-un-bloque.md) | Qué escribe Claude, qué devuelve y sus límites |
| 04 | [De dónde sale el ahorro](04-de-donde-sale-el-ahorro.md) | Las dos fuentes y el mito del 37 % |
| 05 | [Cuándo ahorra](05-cuando-ahorra.md) | Las tareas donde conviene |
| 06 | [Cuándo no ahorra (y es más lento)](06-cuando-no.md) | Archivos locales, lecturas sueltas y filtros que esconden datos |
| 07 | [Mis mediciones](07-mis-mediciones.md) | Lo que muestran mis sesiones reales |
| 08 | [Lo que midieron otros](08-lo-que-midieron-otros.md) | Las pruebas públicas, con su fuente |
| 09 | [Permisos, hooks y seguridad](09-permisos-y-hooks.md) | Qué revisa cada capa y qué queda ciego |
| 10 | [Límites y fallos conocidos](10-limites-y-fallos.md) | Lo que no funciona todavía |
| 11 | [Cómo medirlo en tu proyecto](11-medirlo.md) | Un A/B honesto en una tarde |
| 12 | [Problemas, mitos y balance](12-problemas-y-balance.md) | Lo que falla, lo que circula y mi decisión |

---

## Convenciones

- **Versión:** Claude Code 2.1.330 (la última al 22 de noviembre de 2026). Code Mode cambió mucho en pocos días: las cifras medidas en 2.1.325–2.1.327 pueden no representar la versión actual.
- **Evidencia de cada dato:** **[doc]** documentación oficial o changelog, **[medido]** en mis sesiones, **[publicado]** medición de un tercero con su fuente, **[criterio]** razonamiento sin medición.
- **Tokens procesados:** entrada, más lecturas y escrituras de caché. Las lecturas de caché cuestan mucho menos, así que "menos tokens" no siempre es "menos costo".
- **Fecha de los datos:** noviembre de 2026.

`claude-code` `code-mode` `experimental` `tokens` `mcp` `hooks` `productividad`
