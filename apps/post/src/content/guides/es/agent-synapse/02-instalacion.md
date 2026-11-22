**02**

# Instalar en cada agente

[← Índice](README.md)

---

### Requisitos

- **Python 3.10 o superior.** En Linux y macOS, `python3`; en Windows, `py -3` o `python`. Para fijar otro intérprete, la variable `SYNAPSE_PYTHON`.
- **git** en el `PATH` (el alcance del proyecto se calcula desde git; sin repo, la raíz es la carpeta actual).
- Las versiones mínimas de cada agente de la tabla de abajo.

No hace falta GPU ni dependencias extra: sin Laya, Synapse corre solo con la biblioteca estándar de Python.

### Claude Code

```bash
claude plugin marketplace add bypabloc/agent-plugins
claude plugin install synapse@bypabloc-agents
claude plugin list                       # comprobar
```

Para un solo proyecto, `--scope project`. Para probarlo sin instalar, clona el repo y usa `claude --plugin-dir ./agent-plugin-synapse`.

### Codex, Antigravity y OpenCode

| Agente | Instalación | Cómo decide |
| :-- | :-- | :-- |
| **Codex** ≥ 0.171 | `codex plugin marketplace add bypabloc/agent-plugins` · `codex plugin add synapse@bypabloc-agents` · luego `/hooks` para confiar en los hooks | Bloquea con `deny`. Codex no puede preguntar desde un hook: un `ask` se responde como `deny` con un id, y tú apruebas una sola ejecución en tu terminal ([cap. 10](10-codex-y-windows.md)) |
| **Antigravity** (`agy` ≥ 1.5.4) | `agy plugin install https://github.com/bypabloc/agent-plugin-synapse` | `deny` y `force_ask` nativos. Un error interno pide confirmación, porque en Antigravity un error equivale a permitir |
| **OpenCode** V2 ≥ 2.3 | En `opencode.json`: `"plugins": ["@bypabloc/synapse@git+https://github.com/bypabloc/agent-plugin-synapse.git"]` (opción `{"python": "…"}` para fijar el intérprete) | `throw` para bloquear y `permission.assert` para preguntar. Si Synapse no responde, pregunta |

Codex ata la confianza de los hooks al hash de los scripts: después de cada actualización del plugin hay que volver a aprobarlos en `/hooks`.

### Comprobar que funciona

```bash
python3 <plugin>/scripts/synapse.py doctor
```

Revisa el intérprete, los manifiestos, la versión de cada CLI, el delta de Laya y los logs. Para una prueba de punta a punta, pídele al agente algo que deba bloquearse, por ejemplo borrar una carpeta fuera del proyecto: debe responder con un mensaje `🚫 BLOCKED · Synapse · block_dangerous` y la regla que decidió.

En Claude Code, la skill `synapse-status` resume el modo (reglas deterministas o Laya en GPU/CPU) y las decisiones recientes.

### Dónde quedan las trazas

| Agente | Carpeta |
| :-- | :-- |
| Claude Code | `${CLAUDE_CONFIG_DIR:-~/.claude}/logs/synapse/` |
| Codex, Antigravity, OpenCode | `~/.local/state/synapse/logs/` (en Windows, `%LOCALAPPDATA%\synapse\logs`) |

### Límites por plataforma

- **Windows nativo:** protege rutas y escrituras (incluido `Set-Content` de Codex), pero el análisis de comandos de PowerShell es parcial.
- **Laya** no corre en Windows nativo: necesita sockets Unix. En WSL sí.
- **Codex** no tiene herramienta de lectura: el bloqueo de `.env` se aplica a los comandos de shell.

### En mi caso

Uso los cuatro agentes en la misma máquina, en WSL y en Windows. El monorepo trae un script que, tras cada release, actualiza todas las instalaciones (cada CLI, cada perfil y cada scope de proyecto) y retiene la caché anterior de Codex para las sesiones que siguen abiertas, porque esas sesiones conservan la versión con la que arrancaron. En Codex, además, actualizar sin volver a aprobar en `/hooks` no cuenta como actualizado.

`instalación` `claude-code` `codex` `antigravity` `opencode`
