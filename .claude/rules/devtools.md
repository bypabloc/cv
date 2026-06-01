---
description: "Estandares para scripts de desarrollo en devtools/: estructura de scripts, flags pattern, ruff config autocontenido"
globs: "devtools/**/*.py"
---

# Devtools Development Standards

> Reglas para scripts de desarrollo en devtools/.

## Estructura

- Entry point unico: `devtools/run.py` (plugin loader dinamico)
- Cada script es un paquete: `devtools/<nombre>/`
- Archivos obligatorios por script: `main.py` (logica) + `flags.py` (validacion) + `README.md`
- Utilidades compartidas en `devtools/shared/` y `devtools/utils/`
- Scripts disponibles: `scan`, `docker`, `test_runner`, `verify`, `hooks`,
  `e2e`, `init`, `upgrade_deps`, `serverless`, `cloudflare_setup`,
  `rotate_secrets`, `validate_versions`, `mutation_testing`, `weak_assertion`,
  `harness_init`
- Modulos por script max 300 lineas — partir por dominio cuando crece
  (ver `docker/`, `scan/`, `test_runner/`, `serverless/`, `rotate_secrets/`
  como ejemplo)

## API: posicional vs flags

Convencion fija para que el CLI sea predecible:

- **Scripts con multiples comandos discretos** (`docker`, `serverless`,
  `rotate_secrets`, `cloudflare_setup`) toman comando posicional:
  `docker up`, `serverless deploy`, `rotate_secrets turnstile`,
  `cloudflare_setup trigger`. El comando NO se pasa como `--command=...`.
  `cloudflare_setup` ademas usa `--env=dev|stage|prod` para seleccionar
  el entorno objetivo (default `prod`). Ej: `cloudflare_setup trigger --env=dev`.
- **Scripts mono-comando con parametrizacion** (`scan`, `test_runner`,
  `verify`, `upgrade_deps`, `init`, `hooks`, `e2e`) usan SOLO flags. No
  exponen subcomandos: el script es la unidad. Ej: `test_runner
  --module=pkg-content --type=unit`.

En `flags.py`, los scripts subcommand-style extraen el positional desde
`sys.argv[2:]` con un helper `_extract_positionals` (ver
`devtools/serverless/flags.py` o `devtools/rotate_secrets/flags.py` como
referencia) y declaran su lista `VALID_COMMANDS` / `VALID_SERVICES`. El
nombre normalizado queda en `flags_dict['command']` para que `main.py`
lo dispatchee con un dict-handler.

## Comando unico para tests

Tests se corren via `python devtools/run.py test_runner [flags]`. El viejo
`docker test` fue removido en 2026-05 (Fase 3 del refactor CLI). Si alguien
lo invoca, `docker test` imprime un mensaje de migracion con equivalencias
y exit 1. NUNCA se vuelve a anadir como atajo: una sola fuente de verdad.

## Convenciones de codigo

- Python 3.14 (se ejecuta en local via `devtools/.venv`, NO en Docker)
- devtools es un CLI Python autocontenido: sin acoplamiento al resto del
  monorepo, sin dependencias de las apps Astro ni de sus toolchains
- Ruff config propio: `devtools/ruff.toml` (autocontenido, sin extends, autodetectado cuando cwd=`/app/devtools/`)
- Dependencias propias en `devtools/pyproject.toml` + `devtools/uv.lock` (gestionado por uv)
- Bootstrap automatico: `devtools/run.py` ejecuta `uv sync --frozen --project devtools` la primera vez (o cuando el lockfile cambia) y se re-exec en `devtools/.venv/bin/python`
- Type hints obligatorios en funciones publicas

## Ruff config (devtools-specific)

`devtools/ruff.toml` es un archivo autocontenido (sin `extend`). Contiene
todas las reglas comunes mas estas particularidades de devtools:

- `src = ["."]` (cwd es la raiz del modulo)
- `per-file-target-version`: `devtools/run.py` y `.git-hooks/**/*.py` pinneados a `py313` (corren en Python del shell ANTES del re-exec a Python 3.14 del `.venv`)
- Ignorados globales adicionales: `TRY003` (CLI tools usan mensajes descriptivos en excepciones — son la interfaz de usuario)
- Per-file ignores: `**/*.py` ignora `T20` (`print()` es la interfaz de CLI) y `F401` (imports para re-export en `__init__.py` es comun)
- Tests: `devtools/tests/**/*.py` ignora `S101`, `ANN001`/`201`/`202`, `PLR2004` (magic values en asserts), `INP001` (tests no necesitan `__init__.py`)
- isort known-first-party: `scan`, `docker`, `test_runner`
- isort known-third-party: `git` (GitPython)

## Patron flags.py

- Cada script define sus flags en `flags.py` con validacion
- Retorna un dict tipado con los flags parseados
- Validacion de combinaciones invalidas antes de ejecutar

## Patron main.py

- Funcion `main(flags: dict)` como entry point
- Logging con modulo `logging`, nunca `print()` (excepto en CLI output donde `T20` esta ignorado)
- Exit codes: 0 (ok), 1 (error de usuario), 2 (error interno)

## Testing

- Tests en `devtools/tests/` (si aplican)
- Testear logica pura: parsing de flags, validaciones, transformaciones
- Coverage y formatter obligatorios

## Rotacion de credenciales (rotate_secrets)

El script `devtools/rotate_secrets/` rota o configura credenciales de
servicios externos y las escribe a `docker/env/{server,client}/.{env}`.
Detalle completo: skill `rotate-secrets` o
`devtools/rotate_secrets/README.md`.

Reglas duras:

- Cada servicio es un subcomando posicional con sus credenciales como
  flags **explicitas** (no como env vars, no como path a un `.env`).
  Ej: `rotate_secrets turnstile` exige `--cloudflare-api-token` +
  `--cloudflare-account-id`.
- El script NUNCA lee un archivo `.env` automaticamente
  (ver `.claude/rules/env-files.md`). Si el usuario tiene la credencial
  en `docker/env/dev-cli/.prod`, la extrae con
  `grep -m1 '^KEY=' file | cut -d= -f2-` y la pasa inline.
- Si la rotacion afecta un secret que las Lambdas consumen via SSM,
  sincronizar despues con `serverless setup-ssm`
  (ver `.claude/rules/serverless-secrets.md`).

Servicios soportados: `turnstile`. Receta para agregar uno nuevo en el
README del script y en la skill `rotate-secrets`.

## Cloudflare Pages multi-env (cloudflare_setup)

El script `devtools/cloudflare_setup/` opera los 18 Pages projects del
portfolio (6 niches x 3 envs). Detalle: skill `cloudflare-deploy` o
`devtools/cloudflare_setup/README.md`.

Reglas duras:

- Fase posicional + `--env=dev|stage|prod` (default `prod`). Ej:
  `cloudflare_setup trigger --env=dev`. El env determina el sufijo del
  `project_name` (`-dev`/`-stage` o sin sufijo en prod), la branch
  GitHub que Pages construye (`dev`/`stage`/`main`), el `custom_domain`
  y las env vars per env (`BASE_DOMAIN`, `APEX_DOMAIN` solo en prod,
  `PUBLIC_API_ENDPOINT`, `PUBLIC_TURNSTILE_SITEKEY`, `SITE_URL`).
- Config-as-truth: la fase `projects` reescribe `build_config` +
  `env_vars` segun `config.py`. Cambios manuales en la consola
  Cloudflare se revierten en el siguiente `projects --env=<X>`.
- `run.py` NO auto-carga `tmp/cloudflare-creds.env`. Exportar
  `CLOUDFLARE_API_TOKEN` + `ACCOUNT_ID` antes (`set -a; .
  tmp/cloudflare-creds.env; set +a`) o pasar inline con `grep -m1 '^KEY='`.
- NUNCA llamar a la API REST de Cloudflare con `curl` para operar dev/stage
  pensando que "el script solo conoce prod" — el script ya cubre los 18
  projects. Usar siempre `cloudflare_setup <phase> --env=<X>`.
- Agregar una app nueva: editar `APPS` en `config.py` y correr
  `cloudflare_setup all --env=<X>` para cada env. Agregar un env nuevo:
  agregar entrada a `ENVS` (incluye widget Turnstile per env) + crear
  branch GitHub + correr `all --env=<env>`.

## Backend serverless (serverless)

El script `devtools/serverless/` opera el backend serverless (recursos
compartidos + los Lambdas Python). Detalle: skill `lambda-controller` o
`.claude/docs/serverless-backend/`. Comando posicional + flags
(`--lambda`, `--stage`, `--aws-profile`).

Comandos relevantes: `run`, `deploy`, `destroy`, `status`,
`tests --type=<unit|integration|coverage>`, `lint-deps`,
`provision-infra`, `list-resources`, `setup-ssm`, `sync-secrets`,
`secrets-status`, `seed-email-config`.

- `seed-email-config --stage=<X>` — sube los templates de email a S3 +
  inserta las filas de configuracion en la tabla DynamoDB `email-config`
  (datos del Lambda `send_email`). Reemplaza al flujo SQS eliminado.

> SQS fue eliminado del backend: el subpaquete `shared.queue` ya no
> existe, el trigger `sqs` ya no es valido (solo `direct` y `http`) y el
> recurso `sqs`/`sqs-queue` ya no se provisiona. Recursos compartidos
> provisionables: `dynamodb`, `api_gateway`, `s3`, `secrets`,
> `cloudwatch`.
