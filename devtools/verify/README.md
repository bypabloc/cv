# verify

Dada una lista de archivos modificados/staged en git, retorna las
verificaciones que deberian correrse antes de declarar la feature como
"lista" según `.claude/rules/verify-before-done.md`.

API unificada para que agentes (feature-implementer, hook-fixer) sepan que
correr sin re-parsear las reglas.

## Uso

```bash
# Default: usa archivos all-changed (staged + modified + untracked).
python devtools/run.py verify

# Solo staged.
python devtools/run.py verify --staged

# Solo modificados (sin staged ni untracked).
python devtools/run.py verify --modified

# Listar verificaciones sin ejecutar (default).
python devtools/run.py verify --staged

# Ejecutar todas las verificaciones y reportar resultados.
python devtools/run.py verify --staged --execute

# Output JSON estructurado (util para agentes). El JSON va a stdout
# limpio; banners y bootstrap a stderr, así puedes pipear:
python devtools/run.py verify --staged --json | jq '.files'

# Combinación comun: staged + execute + JSON.
python devtools/run.py verify --staged --execute --json
```

## Flags

| Flag | Default | Proposito |
|------|---------|-----------|
| `--staged` | false | Solo archivos en git index (`git diff --cached`) |
| `--modified` | false | Solo archivos modificados (`git diff`) sin staged |
| `--all-changed` | true (si ningun otro) | Staged + modified + untracked |
| `--execute` | false | Correr cada verificación y capturar exit + output |
| `--json` | false | Output como JSON estructurado |

Solo una de `--staged`, `--modified`, `--all-changed` puede usarse.

## Clasificación de archivos

| Clasificación | Verificaciones |
|---------------|----------------|
| server_model | makemigrations --dry-run + lint + unit tests |
| server_admin | manage.py check + lint |
| server_service | lint + unit tests |
| server_selector | lint + unit tests |
| server_view | lint + integration tests |
| server_serializer | lint + unit tests |
| server_task | lint |
| server_python | lint |
| dashboard_typescript | typecheck + biome lint |
| landing_typescript | typecheck + biome lint |
| devtools_python | pytest devtools/tests/ |
| claude_json | python -m json.tool |
| claude_shell | bash -n |
| test_or_migration_or_init | (skip) |

Verificaciones se deduplican: si 5 archivos del mismo tipo activan el
mismo `lint`, se ejecuta una vez.

## Deteccion de archivos cambiados

`verify` delega la deteccion en `devtools/shared/scan_helper.py`, que
envuelve `scan` (la fuente canonica del proyecto). Mapeo de flags:

| Flag verify | git_mode de scan | Equivale a |
|-------------|------------------|------------|
| `--staged` | `staged` | `git diff --cached` |
| `--modified` | `unstaged` | `git diff` (sin staged) |
| `--all-changed` (default) | `changed` | staged + unstaged + untracked |

Ventajas vs invocar `git` directo:

- Filtra archivos eliminados (`include_deleted=False`) — un path en
  `git diff` que ya no existe en disco no se reporta.
- Respeta `.gitignore` del proyecto.
- Reutiliza el mismo motor que `pre-commit`, `pre-push` y `test_runner`.

## Exit codes

- 0: todas las verificaciones pasaron (o sin --execute)
- 1: alguna verificación fallo (solo con --execute)
- 2: error de invocacion

## Casos de uso

### En un agente autonomo

Tras implementar una feature, antes de commitear:

```bash
python devtools/run.py verify --staged --execute --json > tmp/verify.json
```

Si exit != 0, el agente lee el JSON, identifica que falla y aplica fix.

### En CI

```yaml
- name: Verify staged changes
  run: python devtools/run.py verify --all-changed --execute --json
```

### En slash command /ship

El comando `/ship` invoca `verify --staged --execute` después de TDD y
antes de invocar `hook-fixer` para que las verificaciones especificas del
tipo de cambio se corran primero.
