# rotate_secrets

Rota o configura credenciales de servicios externos y escribe los valores
en `docker/env/{server,client}/.{env}`. Subcommand-style: cada servicio es
un subcomando con sus credenciales propias como flags explicitas.

## Uso

```bash
python devtools/run.py rotate_secrets <servicio> [flags...]
```

Servicios actualmente soportados:

| Servicio | Credenciales requeridas |
| --- | --- |
| `turnstile` | `--cloudflare-api-token`, `--cloudflare-account-id` |

## Flags comunes

| Flag | Default | Que hace |
| --- | --- | --- |
| `--dry-run` | `false` | No escribe en disco ni en el servicio externo |
| `--envs=a,b,c` | `local,test,dev,prod` | Subset de envs a actualizar |
| `--force` | `false` | (turnstile) Crear widget nuevo aunque exista uno con el mismo nombre |
| `--rotate` | `false` | (turnstile) Rotar el secret de widgets existentes |

## Politica de credenciales

NUNCA se leen archivos `.env` automaticamente: el usuario extrae solo la
key requerida con `grep -m1 ^KEY= file | cut -d= -f2-` y la pasa inline al
comando (ver `.claude/rules/env-files.md`). El script NO acepta paths a
archivos `.env` como flag.

## Servicio: turnstile

Configura los 3 widgets Cloudflare Turnstile que cubren los entornos del
portfolio:

- `Portfolio Backend (dev)`  -> usado por `.local`, `.test`, `.dev`
- `Portfolio Backend (prod)`  -> usado por `.prod`

Cada widget cubre los hostnames del estandar de subdominios
(`{niche}.portfolio.{env}.the-full-stack.com` + apex + localhost para dev).

Para cada env target:

- `docker/env/server/.{env}` <- `TURNSTILE_SECRET_KEY`
- `docker/env/client/.{env}` <- `PUBLIC_TURNSTILE_SITEKEY`, `TURNSTILE_SITE_KEY`

El bypass de Turnstile para tests E2E ya NO se gestiona aca: es un token
Ed25519 firmado cuyas claves genera `bypass_token keygen` (ver
`devtools/bypass_token/README.md`). Este script solo rota el secret REAL
del widget Cloudflare + el sitekey publico.

### Ejemplos

Setup inicial (reusa widgets existentes, lee secrets, escribe envs):

```bash
python devtools/run.py rotate_secrets turnstile \
  --cloudflare-api-token="$(grep -m1 '^CLOUDFLARE_API_TOKEN=' \
      docker/env/dev-cli/.prod | cut -d= -f2-)" \
  --cloudflare-account-id="$(grep -m1 '^CLOUDFLARE_ACCOUNT_ID=' \
      docker/env/dev-cli/.prod | cut -d= -f2-)"
```

Rotar TODOS los secrets (por compromiso o rotacion periodica):

```bash
python devtools/run.py rotate_secrets turnstile \
  --cloudflare-api-token="$(...)" \
  --cloudflare-account-id="$(...)" \
  --rotate
```

Dry-run solo para inspeccionar lo que haria:

```bash
python devtools/run.py rotate_secrets turnstile \
  --cloudflare-api-token="$(...)" \
  --cloudflare-account-id="$(...)" \
  --dry-run
```

Solo actualizar el env de dev:

```bash
python devtools/run.py rotate_secrets turnstile \
  --cloudflare-api-token="$(...)" \
  --cloudflare-account-id="$(...)" \
  --envs=dev \
  --rotate
```

### Siguiente paso post-rotacion

Tras rotar, sincronizar el `TURNSTILE_SECRET_KEY` a SSM Parameter Store
para que las Lambdas lo lean en runtime:

```bash
python devtools/run.py serverless setup-ssm \
  --name=/portfolio/<stage>/turnstile-secret
```

## Agregar un servicio nuevo

1. Crear `devtools/rotate_secrets/<servicio>.py` con una funcion `run(...)`.
2. Agregar el servicio a `VALID_SERVICES` y `_REQUIRED_CREDS` en `flags.py`.
3. Agregar `_COMMAND_SUMMARIES[<servicio>]` y `_COMMAND_FLAGS[<servicio>]`.
4. Agregar el handler a `_DISPATCH` en `main.py`.
5. Agregar la fila correspondiente a la tabla "Servicios" de este README.

Cada servicio decide que credenciales pide (siempre como flags) y que
archivos `.env` toca.
