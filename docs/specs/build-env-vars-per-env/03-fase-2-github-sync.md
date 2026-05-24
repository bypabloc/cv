# 02 — Fase 1: script `devtools/github_sync`

## Objetivo

Crear `python devtools/run.py github_sync --env=<dev|stage|prod>` que
lee `docker/env/client/.{env}` y publica cada `PUBLIC_*` (y selectas no-
prefixed como `BASE_DOMAIN`, `BASE_SCHEME`, `APEX_DOMAIN`) como GitHub
Environment Variable en el environment `<env>`.

Cumple AC-4, AC-5, AC-6, AC-7.

## Diseno

### Estructura

```
devtools/github_sync/
├── __init__.py        # re-exports
├── main.py            # def main(flags: dict) — orquesta
├── flags.py           # parsing + validacion de --env, --dry-run, --keys
├── parser.py          # parser de .env (sin volcar)
├── gh_client.py       # wrapper de `gh variable list/set/delete --env`
└── README.md
```

### Reglas duras

- **NUNCA** imprimir el valor de una key. La salida son lineas tipo
  `[PUSH] PUBLIC_API_ENDPOINT` o `[SKIP] BASE_DOMAIN` — sin el valor.
- **NUNCA** copiar el contenido del `.env` a una variable global ni a
  un tempfile sin permisos `0600`. El parser entrega un dict en memoria
  y se descarta tras procesar.
- **SIEMPRE** comparar valor local vs remoto antes de hacer PUSH (via
  hash SHA256 — mismo patron que `serverless/secrets_sync.py`).
- **SIEMPRE** usar `gh variable set NAME --env <env> --body "<value>"`
  con el valor pasado por argumento. `gh` lo manda al API por HTTPS, no
  queda en logs (los Variables NO se mascarean pero tampoco se
  imprimen automaticamente por el CLI en operaciones de set).
- **SIEMPRE** fallar con exit code != 0 si `gh auth status` reporta no
  autenticado, si el environment `<env>` no existe, o si el archivo
  `.env` no existe.
- **NUNCA** atribuir a IA en docstrings, commits, ni mensajes.

### Flags

| Flag | Required | Default | Descripcion |
|------|----------|---------|-------------|
| `--env` | si | — | `dev`, `stage` o `prod`. Mapea a `docker/env/client/.{env}` y al GH Environment del mismo nombre |
| `--dry-run` | no | `false` | No ejecuta `gh variable set`; solo reporta PUSH/SKIP/CREATE/MISSING |
| `--keys` | no | (todas las del catalogo) | Subset de keys a sincronizar, separadas por coma |
| `--create-env` | no | `false` | Si el GH Environment no existe, lo crea via `gh api repos/:owner/:repo/environments/<env> -X PUT` |

### Catalogo de keys sincronizadas

Solo las keys que afectan el build de las apps Astro. Las que son
solo-local (puerto Docker, flags de CI) se ignoran:

| Key | Categoria | Notas |
|-----|-----------|-------|
| `BASE_DOMAIN` | URL builder | `portfolio.{env_prefix}the-full-stack.com` |
| `BASE_SCHEME` | URL builder | siempre `https` (podria omitirse, pero por consistencia) |
| `APEX_DOMAIN` | URL builder | solo en prod (vacio en dev/stage) |
| `PUBLIC_API_ENDPOINT` | API Gateway | `https://api.portfolio.{env_prefix}the-full-stack.com` |
| `PUBLIC_TURNSTILE_SITEKEY` | Turnstile | 1 widget por env |

Keys **ignoradas** (no se sincronizan): `PROXY_PORT`, `BASE_PORT`, `CI`,
`TURNSTILE_SITE_KEY` (duplicada de `PUBLIC_TURNSTILE_SITEKEY`),
`TURNSTILE_ENABLED` (siempre `true` en envs deployados).

El catalogo vive en `devtools/github_sync/catalog.py` como un set de
strings — facil de extender cuando aparezca una nueva PUBLIC_* key.

### Flujo de ejecucion

```
1. validar flags (--env requerido y valido)
2. verificar `gh auth status` -> exit 1 si no auth
3. verificar que docker/env/client/.{env} existe -> exit 1 si no
4. parser.py lee el .env y devuelve {key: value} solo para keys del catalogo
5. para cada key del catalogo:
   a. resolver valor local (puede estar vacio: en ese caso es MISSING)
   b. resolver valor remoto: `gh variable get <KEY> --env <env>` (silencioso)
   c. comparar via hash:
      - local vacio + remoto vacio -> MISSING (skip silencioso)
      - local == remoto             -> SKIP
      - local != remoto             -> PUSH (gh variable set ...)
      - local con valor + remoto inexistente -> CREATE (gh variable set ...)
6. imprimir resumen: N PUSH, N SKIP, N CREATE, N MISSING
7. exit 0
```

### Tests

`devtools/tests/unit/test_github_sync.py` cubre:

- AC-4: parser extrae correctamente `PUBLIC_*` y `BASE_*` de un .env
  con keys mezcladas.
- AC-5: ejecutar dos veces con el mismo `.env` y mock de `gh variable
  get` que devuelve el mismo valor -> segunda corrida reporta todo SKIP.
- AC-6: si el valor local cambia, reporta PUSH y llama a `gh variable set`
  exactamente una vez. La salida capturada NO contiene el valor.
- AC-7: si `gh auth status` falla, el script sale con exit code 1 y
  mensaje "GitHub CLI no autenticado".
- Caso extra: si el `.env` no existe, exit 1 con mensaje claro.
- Caso extra: si `--keys=BASE_DOMAIN,PUBLIC_API_ENDPOINT` se pasa, solo
  sincroniza esas dos.

Mocks: `subprocess.run` para `gh`. NUNCA correr `gh` real en tests.

## Archivos

### Crear

- `devtools/github_sync/__init__.py` — re-exports de `main`, `flags`
  - Verificar: `python -c "from devtools.github_sync import main; print(main)"`
- `devtools/github_sync/main.py` — orquestador (def main(flags: dict))
  - Verificar: `python devtools/run.py github_sync --env=dev --dry-run`
- `devtools/github_sync/flags.py` — parser de flags
  - Verificar: test unit cubre validacion de `--env` invalido
- `devtools/github_sync/parser.py` — parser de .env (in-memory)
  - Verificar: test unit con fixtures de `.env` minimo
- `devtools/github_sync/gh_client.py` — wrapper de `gh variable {get,set,list}`
  - Verificar: test unit con mock de `subprocess.run`
- `devtools/github_sync/catalog.py` — set de keys del catalogo
  - Verificar: test unit valida que el catalogo coincide con `.example`
- `devtools/github_sync/README.md` — uso, flags, ejemplos
- `devtools/tests/unit/test_github_sync.py` — 6+ tests (los del AC arriba)
  - Verificar: `python devtools/run.py test_runner --module=devtools --type=unit`

### Modificar

- `devtools/run.py` — registrar el nuevo script en el plugin loader
  (si el loader es por convencion de carpetas, no hace falta tocar)
  - Verificar: `python devtools/run.py --help` lista `github_sync`

## Tests Requeridos

### 6.B. Unit Tests (Vitest/pytest)

| Test | AC |
|------|-----|
| `test_parser_extracts_only_catalog_keys` | AC-4 |
| `test_idempotent_run_reports_all_skip` | AC-5 |
| `test_value_change_triggers_push_without_logging_value` | AC-6 |
| `test_missing_gh_auth_exits_with_clear_message` | AC-7 |
| `test_missing_env_file_exits_with_clear_message` | AC-7 |
| `test_keys_flag_filters_subset` | (caso extra) |
| `test_catalog_matches_dot_example_keys` | invariante: catalogo sincronizado con .example |

### 6.C. Typecheck

- `python -m compileall -q devtools/github_sync` debe pasar
- Ruff: `cd devtools && uv run ruff check github_sync/`

## Verificacion incremental (al final de la Fase 1)

```bash
# El script existe y arranca
python devtools/run.py github_sync --help

# Dry-run desde el .dev local — sin tocar GH, sin imprimir valores
python devtools/run.py github_sync --env=dev --dry-run

# Tests pasan
python devtools/run.py test_runner --module=devtools --type=unit

# Ruff/format limpio
cd devtools && uv run ruff check github_sync/ && uv run ruff format --check github_sync/
```
