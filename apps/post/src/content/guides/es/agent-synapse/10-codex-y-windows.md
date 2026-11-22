**10**

# Codex y Windows: lo que costó horas

[← Índice](README.md)

---

### El ask de Codex

Codex no tiene un diálogo de confirmación desde un hook: solo puede permitir o denegar. Synapse lo resuelve así:

1. Un `ask` se emite como `deny` con un id de un solo uso.
2. **Tú** apruebas esa ejecución en tu terminal (el agente no puede hacerlo):

```bash
python3 <plugin>/scripts/synapse.py approve <id>
```

3. El agente reintenta el comando y esta vez pasa. La aprobación vence y no se reutiliza.

Una regla dedicada (`self_approval`) bloquea cualquier intento del agente de ejecutar ese `approve` por su cuenta.

### El incidente: 4 h 27 min y un archivo Markdown

En una sesión de Codex en Windows, tras 4 h 27 min de trabajo autónomo, un `apply_patch` de documentación incluyó un archivo de reglas en Markdown de la carpeta `.agents/rules/`. Synapse lo trató como configuración del agente y respondió `deny` pidiendo aprobación. El agente dejó de trabajar, me pidió el `approve` y quedaron dos tareas sin hacer hasta que volví. Además, el motivo se veía con caracteres rotos (`Synapse � protect_files … Configuraci�n`).

| Causa | Arreglo (1.7.1) |
| :-- | :-- |
| Toda la carpeta de reglas se trataba como gobierno del host, aunque los `.md` son instrucciones como `AGENTS.md` | Un `.md` en esa carpeta pasa; el resto sigue en `ask` |
| El texto del `deny` decía "informa al usuario y espera su respuesta", y el agente obedeció | El texto pide aplicar aparte lo que no depende del archivo, seguir trabajando y pedir la aprobación al cerrar el turno |
| La salida usaba la codificación de la consola (cp1252) y Codex lee UTF-8 | stdin, stdout y stderr en UTF-8 explícito |

**La lección:** en Claude Code, un `ask` cuesta un clic. En Codex detiene al agente hasta que vuelves, aunque lleve horas trabajando solo. Cada `ask` en Codex tiene que justificar ese costo, y el `deny` debe decirle al agente cómo seguir sin rodear la regla.

### Un --help que detenía al agente

El agente quiso ver la ayuda de otro CLI (`codex exec --help`). La regla `agent_wrapper`, que pide confirmación al lanzar otro agente en modo no interactivo, lo trató como un agente lanzado y quedó esperando. Desde la 1.7.2, `--help`, `-h`, `--version` y `-V` no cuentan: el CLI imprime y sale sin correr nada. `codex exec 'prompt'` sigue en `ask`, y con `--dangerously-*`, `--yolo` o `--full-auto`, en `block`.

### Windows: el python3 de la tienda

En Claude Code en Windows, cada herramienta mostraba `PreToolUse:Edit hook failed` con un mensaje de "no se encontró Python; ejecutar sin argumentos para instalar desde el Microsoft Store". `python3` resolvía al acceso directo de la tienda aunque hubiera un Python real. Y un hook que falla **no bloquea**: Synapse no revisaba nada.

El arreglo (1.7.2): todos los hooks pasan por un lanzador (`run-hook.cmd`) que busca un Python real, conserva el exit 2 con que Claude Code bloquea y, si no encuentra Python, responde `ask` en vez de nada. En Linux y macOS el lanzador hace `exec` del mismo `python3`, así que la salida no cambia.

### En mi caso

Los dos fallos de Windows tenían algo en común: el agente seguía avanzando, así que nada parecía roto. Desde entonces, la vigilancia del monorepo trata un `hook failed` como hallazgo aunque la sesión siga, y revisa que cada script de hook declarado exista (un hook que apunta a un clon borrado falla en silencio en cada herramienta).

`codex` `windows` `aprobaciones` `incidentes`
