# Hooks de Claude Code

> Hooks bash versionados que el harness de Claude Code dispara en
> distintos puntos del ciclo de vida. Configurados en `.claude/settings.json`.
> Helpers compartidos en `_lib.sh`. Proyecto: portfolio (Astro 6 + pnpm).

## Tabla de hooks activos

| Hook | Matcher | Tipo | Bloquea? | Que hace |
|------|---------|------|----------|----------|
| `protect-sensitive.sh` | `Edit\|Write\|MultiEdit` | PreToolUse | Si | Bloquea edicion de `.env*`, secrets, `.git-hooks/`, `.git/config`, claves crypto |
| `protect-bash.sh` | `Bash` | PreToolUse | Si | Bloquea redirects a `.env`, pipes a shell remoto, `--no-verify`, `chmod 777`, in-place edits a lockfiles |
| `protect-branch.sh` | `Bash` | PreToolUse | Si | Bloquea `git commit/push/merge` si HEAD esta en rama protegida (master/main/dev/release) |
| `format-on-save.sh` | `Edit\|Write\|MultiEdit` | PostToolUse | No | Auto-format con Biome (`pnpm exec biome format --write`) |
| `lint-check.sh` | `*` | PostToolBatch | No | Lint check rapido con Biome sobre archivos modificados (incluye untracked) |
| `verify-state.sh` | `*` | Stop | No | Lista archivos cambiados, mirrors faltantes (`src/<X>` -> `tests/unit/<X>`), comandos de verificacion sugeridos |
| `progress-cleanup.sh` | `*` | Stop | No | Sugiere limpieza de scratchpads en `docs/progress/` |
| `agent-memory-reminder.sh` | `*` | SubagentStop | No | Avisa si subagente termino sin actualizar `agent-memory/<agente>/MEMORY.md` |
| `pre-compact-snapshot.sh` | `auto\|manual` | PreCompact | No | Snapshot de `docs/progress/current.md` antes de compactacion |
| `session-start-context.sh` | `compact` | SessionStart | No | Re-inyecta reglas criticas tras compactacion |
| `session-start-check.sh` | `startup` | SessionStart | No | Verifica pnpm + node_modules + rama actual al inicio |

## Helpers en `_lib.sh`

- `read_file_path_from_stdin` — extrae `tool_input.file_path` del payload
- `read_command_from_stdin` — extrae `tool_input.command` del payload (Bash)
- `current_branch` — retorna nombre de rama actual
- `on_protected_branch` — true si rama es master/main/dev/release
- `have_pnpm` — true si pnpm esta en PATH
- `hook_log <msg>` — log al stderr con prefijo

Variables exportadas: `PROJECT_NAME=portfolio`, `CLAUDE_PROJECT_DIR`.

## Test manual de hooks

Los hooks bash no tienen suite automatica. Validacion manual:

### protect-bash

```bash
# Bloquea redirect a .env
printf '%s' '{"tool_input":{"command":"echo X > .env"}}' \
  | .claude/hooks/protect-bash.sh
echo "exit: $?"  # esperado: 2

# Bloquea --no-verify
printf '%s' '{"tool_input":{"command":"git commit --no-verify"}}' \
  | .claude/hooks/protect-bash.sh
echo "exit: $?"  # esperado: 2

# Permite comandos seguros
printf '%s' '{"tool_input":{"command":"git status"}}' \
  | .claude/hooks/protect-bash.sh
echo "exit: $?"  # esperado: 0
```

### protect-branch

```bash
# Estando en rama protegida, bloquea commit
git checkout main
printf '%s' '{"tool_input":{"command":"git commit -m test"}}' \
  | .claude/hooks/protect-branch.sh
echo "exit: $?"  # esperado: 2

# Estando en feature branch, permite commit
git checkout -b feature/test-branch
printf '%s' '{"tool_input":{"command":"git commit -m test"}}' \
  | .claude/hooks/protect-branch.sh
echo "exit: $?"  # esperado: 0
git checkout - && git branch -D feature/test-branch  # cleanup
```

### verify-state

```bash
# Sin cambios git, debe ser silencioso
.claude/hooks/verify-state.sh
echo "exit: $?"  # esperado: 0, sin output

# Con cambios git, debe sugerir verificaciones
touch src/foo.ts
.claude/hooks/verify-state.sh
# esperado: stderr con sugerencia de mirror tests/unit/foo.test.ts
rm src/foo.ts
```

### session-start-check

```bash
.claude/hooks/session-start-check.sh
# esperado: stderr con estado de pnpm + node_modules + rama
```

## Regla critica: no bloquear el flujo si pnpm esta caido

Hooks PostToolUse y PostToolBatch (format/lint) DEBEN tolerar pnpm ausente
(usar `have_pnpm` antes de invocarlo). El usuario debe poder editar archivos
sin tener pnpm instalado, recibir un warning, y resolver despues.

Hooks PreToolUse (protect-*) NO necesitan pnpm — solo parsean el comando o
path que se va a ejecutar.

## Como agregar un hook nuevo

1. Crear el script en `.claude/hooks/<nombre>.sh` con `#!/bin/bash` + `set -u`
2. Hacerlo ejecutable: `chmod +x .claude/hooks/<nombre>.sh`
3. Source `_lib.sh` para reusar helpers
4. Registrarlo en `.claude/settings.json` -> `hooks` -> matcher correcto
5. Agregar test manual a este README
6. Validar JSON: `python3 -m json.tool .claude/settings.json > /dev/null`
