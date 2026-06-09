# e2e — orquestador unificado de los E2E del portfolio

> Comando monocommand (Python 3.14) que corre los tests E2E del portfolio
> contra el entorno DESPLEGADO (dev, NUNCA prod) via pytest.
> Unifica los dos sistemas viejos (`api_e2e` Python + la suite Playwright
> TypeScript `tests/feature/`) en UNA sola fuente de verdad.

## Modulos (first-class)

| Modulo | Que prueba | Runtime |
|--------|-----------|---------|
| `api` | Los 5 Lambdas HTTP (cv, contact_form, tracking_pixel, auth, users): exito + errores, con tiempos | httpx puro (sin browser) |
| `admin` | Flujos completos del panel admin (login/logout/forms/MFA), 100% reales | browser (playwright-python) |
| `app` | Las 6 apps Astro desplegadas: smoke + navbar + contact + tracking + screenshots | browser (playwright-python) |

Ausente `--module` -> corre los 3 en orden (`api` -> `admin` -> `app`).

## Uso

Requiere SSO activo del perfil para los modulos `api`/`admin`:
`aws sso login --profile tfs-dev`.

```bash
# Los 3 modulos contra dev
python devtools/run.py e2e --env=dev --aws-profile=tfs-dev

# Solo el modulo api
python devtools/run.py e2e --module=api --env=dev --aws-profile=tfs-dev

# Un solo Lambda del modulo api
python devtools/run.py e2e --module=api --lambda=auth --env=dev \
  --aws-profile=tfs-dev

# Solo el modulo app (no requiere auth)
python devtools/run.py e2e --module=app --env=dev

# Browser admin/app visible en host (debug, sin container)
python devtools/run.py e2e --module=admin --env=dev --headed \
  --aws-profile=tfs-dev

# Conservar los datos sinteticos creados (no limpiar Neon)
python devtools/run.py e2e --module=api --env=dev --keep-data \
  --aws-profile=tfs-dev
```

## Flags

| Flag | Default | Descripcion |
|------|---------|-------------|
| `--module` | (los 3) | `api` / `admin` / `app`. Ausente -> los 3 en orden |
| `--env` | `dev` | Entorno de deploy: `dev` (NUNCA prod) |
| `--samples` | `5` | Muestras por endpoint read-safe del modulo `api` (>= 1) |
| `--aws-profile` | (shell) | Perfil AWS CLI para SSM/Neon (ej. `tfs-dev`) |
| `--keep-data` | `false` | No limpiar los datos sinteticos creados en Neon |
| `--lambda` | (todos) | Sub-filtro del modulo `api` (cv/contact_form/.../users) |
| `--headed` | `false` | Browser visible (admin/app, debug local sin container) |
| `--verbose` / `--quiet` | — | Verbosidad |

## Como funciona

1. **Gate de auth duro (AC-6)**: si se pide `api` o `admin` (incluido el
   modo "los 3"), exige SSO valido (`sts get-caller-identity` con el
   `--aws-profile`) Y clave privada de bypass Ed25519 disponible en
   `docker/env/dev-cli/.{env}`. Si falta algo -> error claro + exit 2.
   El modulo `app` (no-auth) NO dispara el gate.
2. **Por cada modulo pedido** (`api` -> `admin` -> `app`):
   - `api` -> `pytest tests/api/` en proceso (httpx puro, sin browser),
     pasando `--env/--aws-profile/--samples/--keep-data/--lambda` como
     opciones de pytest (las parsea `tests/conftest.py`).
   - `admin`/`app` -> levanta el container Docker `e2e` (profile `e2e`,
     espera el sentinel `/tmp/.e2e-ready`) y corre `pytest tests/<module>/`
     DENTRO del container. Con `--headed` corre local (sin container) si
     hay browsers en el host.
   - Si `tests/<module>/` aun no existe (otra fase del plan), el comando
     degrada con un `[INFO] ... aun no implementado` SIN romper.
3. **Exit codes**: `0` (todos PASS), `1` (algun modulo FALL), `2` (error de
   setup/auth).

## Hermetico (secretos)

Ningun valor de secreto (clave privada de bypass, Neon URL) se imprime jamas
en stdout/stderr. El gate de auth solo reporta presencia/ausencia. Cumple
[`.claude/rules/env-files.md`](../../.claude/rules/env-files.md).

## Container Docker `e2e`

`docker/dockerfiles/{local,dev,test}/e2e/Dockerfile` + el servicio `e2e`
(profile `e2e`) en `docker/docker-compose/{local,dev,test}.yml`. Imagen base
Python 3.14 (slim) + `playwright install --with-deps chromium webkit`. El
container corre contra el backend desplegado: `network_mode: host` (salida a
internet), monta el repo en `/app` y `~/.aws` read-only para SSM. El
entrypoint (`docker/scripts/e2e-entrypoint.sh`) crea `/tmp/.e2e-ready` y deja
el container vivo.

## Estructura

```text
e2e/
├── main.py        # orquesta los modulos (gate de auth + run por modulo)
├── flags.py       # validacion de flags + describe()
├── runner.py      # gate de auth duro + runner por modulo (proceso/container)
├── container.py   # lifecycle del container Docker `e2e` (ensure + pytest)
└── README.md      # este archivo
```

Las herramientas compartidas (cliente HTTP, secretos, seed/cleanup Neon,
harness browser playwright-python, reporter) viven en `tests/shared/`
(portador E2E). Los tests por modulo viven en `tests/{api,admin,app}/`.

## Reglas (rule + skill)

La arquitectura E2E completa se documenta en la rule
`.claude/rules/e2e-testing.md` + la skill `e2e-testing` (fase G del plan
`docs/specs/e2e-refactor/`).
