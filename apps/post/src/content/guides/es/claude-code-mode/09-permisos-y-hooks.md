**09**

# Permisos, hooks y seguridad

[← Índice](README.md)

---

### Cada llamada interna pasa por tus reglas

Dentro de un bloque, cada llamada a una herramienta pasa por las reglas `deny` y `ask` y por los hooks `PreToolUse` **con su nombre normal** (`Bash`, `Read`, `mcp__servidor__herramienta`) **[doc]**. Un guardrail que ya tenías sigue funcionando: no hace falta reescribirlo para Code Mode.

Dos consecuencias prácticas:

- **Más invocaciones de hooks.** Un bloque que lee 500 archivos dispara 500 veces tus hooks de lectura. Hooks lentos se notan, y bajo carga pueden agotar su tiempo.
- **Comandos compuestos.** Un `git push` dentro de una carpeta puede llegar al hook como `cd 'app' && git push`: el hook debe revisar cada parte.

### Auto mode: el clasificador revisa el script, no los valores

En auto mode, el clasificador revisa **cada bloque antes de ejecutarlo**, no cada llamada. No ve los valores que se calculan durante la ejecución, como una ruta que sale de una búsqueda **[doc]**. Para las operaciones críticas, mantén reglas `ask` o hooks propios: ellos sí ven cada llamada con sus argumentos reales.

### El sandbox cubre solo la shell

El sandbox de shell aplica a los comandos que lanza el script. El JavaScript y sus llamadas a archivos, web y MCP corren **fuera del sandbox**. Para aislar todo, la documentación recomienda un contenedor o una VM **[doc]**.

### Qué pasa si un hook falla

Desde 2.1.329, si un hook `PreToolUse` falla (no por timeout ni por decisión), **la llamada se ejecuta por defecto**. Para que un guardián falle cerrado hay que declarar `"onFailure": "block"` en hooks de tipo `command` o `http` **[doc]**. Antes de 2.1.329 era al revés, así que guías escritas en los primeros días dicen que Code Mode "falla cerrado": ese dato quedó viejo.

### Revisar o aprobar los scripts

| Quieres | Cómo |
| :-- | :-- |
| Aprobar cada script antes de que corra | `"permissions": { "ask": ["REPL"] }` (el prompt no muestra el código: ábrelo con `Ctrl+O`) |
| Revisar el código con un hook | `PreToolUse` con matcher `REPL`, leyendo `tool_input.code` |
| Redactar lo que vuelve al modelo | `PostToolUse` con matcher `REPL`, devolviendo `updatedToolOutput` |
| Confirmar comandos críticos | Reglas `ask` como `Bash(git push *)` |

### En mi caso

Uso [Synapse](https://post.the-full-stack.com/agent-synapse/), mis guardrails como hooks `PreToolUse`, y funcionó sin cambios: mientras escribía esta guía, un bloque de Code Mode intentó correr `git` sobre un repo fuera del proyecto y Synapse lo bloqueó con su regla de siempre, aunque la llamada venía dentro de un script. Lo mismo con session-handoff: sus avisos tras cada escritura llegaron igual desde dentro de los bloques. Lo que sí revisé fue que mis hooks guardianes declararan `onFailure: "block"`.

`seguridad` `hooks` `permisos` `auto-mode`
