**06**

# Configurar por proyecto

[← Índice](README.md)

---

### Comandos rutinarios

Los sub-comandos que empiezan con alguno de estos prefijos se tratan como desarrollo rutinario: Laya no los evalúa y la decisión es `pass`. Las reglas de bloqueo y confirmación siguen aplicando antes.

`.synapse/commands.json` (con respaldo en `.claude/synapse-commands.json`):

```json
{ "routine_commands": ["bun devtools/run.ts", "graphify"] }
```

Editar este archivo pide confirmación: es configuración de seguridad.

Sin declarar nada, ya cuentan como rutina `bun|npm|pnpm run|test`, `uv run <herramienta>`, `python -m pytest`, los scripts versionados del proyecto, `git -C`, `git worktree list|add` y `gh pr|run|issue` (no `merge`).

### Proponer la lista desde la traza

```bash
python3 <plugin>/scripts/learn_from_log.py --project ~/code/mi-app --replay
```

Resume las decisiones del proyecto, las reproduce con la versión actual y sugiere prefijos para `routine_commands`. Es la forma de convertir las confirmaciones repetidas en reglas, en vez de aprobarlas a mano cada vez.

### Variables de entorno

Se definen en el `env` de la configuración del agente (en Claude Code, `settings.json` global o del proyecto):

| Variable | Qué hace | Por defecto |
| :-- | :-- | :-- |
| `SYNAPSE_LAYA` | `on` enciende Laya; `off` la apaga en todos los hooks | Sin definir: Laya apagada |
| `SYNAPSE_LAYA_HOOKS` | Hooks donde corre Laya, separados por comas | Vacía |
| `SYNAPSE_LOG_DIR` | Carpeta de la traza | La del agente ([cap. 02](02-instalacion.md)) |
| `SYNAPSE_LOG_RETENTION_DAYS` | Días que se conservan las trazas (`0` = todo) | `30` |
| `SYNAPSE_DEBUG` | Mensajes de diagnóstico en stderr | `0` |
| `SYNAPSE_PYTHON` | Intérprete a usar | El que encuentre el lanzador |
| `SYNAPSE_LAYA_IDLE_SECONDS` | Inactividad tras la que el daemon de Laya libera la VRAM | `1200` |
| `SYNAPSE_LAYA_STARTUP_SECONDS` | Espera máxima al arranque del daemon | `40` |

### Capas nativas que conviene sumar

Synapse es una capa más, no la única. Cada agente tiene controles propios que se complementan bien:

| Agente | Capa nativa recomendada |
| :-- | :-- |
| Codex | Sandbox `workspace-write` y `"**/*.env" = "deny"` en el perfil de permisos |
| Antigravity | Sandbox activo y `permissions.deny` para `read_file(**/.env)` |
| OpenCode | `permission.read["*.env"] = "deny"` y `external_directory = "ask"` |

### En mi caso

Las reglas de rutina que hoy vienen de fábrica salieron así: en la traza de un mes de un proyecto, los únicos `ask` que quedaban eran comandos inofensivos (`bun run typecheck`, `git worktree list`, `pdfinfo`, un `timeout N tail -f /dev/null`). Cada uno pasó a ser una regla o un prefijo de rutina, con un caso que lo fija, y las confirmaciones de ese proyecto casi desaparecieron sin tocar ninguna regla de bloqueo.

`configuración` `variables` `rutina`
