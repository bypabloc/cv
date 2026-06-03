# 04 — Fase B: comando `devtools/e2e/` + container Docker `e2e`

[<- 03 fase shared](03-fase-shared.md) | [Siguiente: 05 modulo api ->](05-fase-modulo-api.md)

> El orquestador. Monocommand `e2e --module=<api|admin|app>`. Sigue las
> convenciones de `devtools.md` (flags.py + main.py + README.md, max 300
> lineas/archivo). Se auto-registra en `run.py` por convencion (carpeta con
> `main.py`).

## B.1 — `devtools/e2e/` (estructura)

```text
devtools/e2e/
├── __init__.py
├── main.py        # def main(flags) -> int: resuelve secretos, decide runner,
│                  #   invoca pytest tests/<module>, imprime resumen tiempos
├── flags.py       # validacion: --module, --env, --samples, --aws-profile,
│                  #   --keep-data, --lambda, --headed, --verbose/--quiet
├── pytest_plugin.py  # opcional: plugin que recolecta CaseResult -> reporter
└── README.md      # uso, flags, como funciona (apunta a la rule)
```

## B.2 — Flags (monocommand, ver `devtools.md`)

| Flag | Default | Descripcion |
|------|---------|-------------|
| `--module` | (todos) | `api` / `admin` / `app`. Ausente -> los 3 en orden |
| `--env` | `dev` | `dev` o `stage` (NUNCA prod) |
| `--samples` | `5` | Muestras por endpoint read-safe (modulo api) |
| `--aws-profile` | (shell) | Perfil AWS CLI para SSM/Neon (ej. tfs-dev) |
| `--keep-data` | `false` | No limpiar datos sinteticos en Neon |
| `--lambda` | (todos) | Sub-filtro del modulo api (cv/contact_form/.../users) |
| `--headed` | `false` | Browser visible (admin/app, debug local) |
| `--verbose`/`--quiet` | — | Verbosidad |

Validacion (reusa la de `api_e2e/flags.py`): `--env in {dev,stage}` (prod
prohibido, AC-5), `--module in {api,admin,app}` (o None), `--samples >= 1`.

## B.3 — `main.py`: orquestacion

```text
main(flags):
  1. valida SSO + clave bypass si module in {api, admin} -> si falta: exit 2
     (AC-6: fallar duro). module=app NO lo exige.
  2. resuelve secretos via tests.shared.secrets (Environment) — hermetico.
  3. para cada module pedido (api / admin / app):
       - api  -> corre pytest tests/api/ (sin browser)
       - admin/app -> ensure_e2e_container() (levanta container `e2e`),
                      corre pytest tests/<module>/ DENTRO del container
                      (o local con --headed si hay browsers en host)
  4. el Reporter (tests.shared.reporter) acumula CaseResult -> imprime
     el resumen de tiempos (cold por Lambda + warm por caso) + veredicto.
  5. cleanup de datos sinteticos (salvo --keep-data) via tests.shared.db.
  6. exit 0 si todos PASS, 1 si algun FAIL, 2 si error de setup.
```

Reusar literalmente la logica de `api_e2e/main.py` para el flujo api
(setup, bypass note, cleanup, reporter). Lo nuevo es el branch browser
(admin/app) que levanta el container.

## B.4 — Cómo pytest recibe la config

Opciones (decidir en impl):

- **A (recomendada)**: `e2e/main.py` invoca
  `pytest tests/<module> --env=<X> --aws-profile=<Y> --samples=N ...` como
  subprocess; `tests/conftest.py` parsea esas opciones con
  `pytest_addoption` y expone fixtures (`env`, `http`, `environment`,
  `reporter`). El resumen de tiempos lo imprime un plugin pytest
  (`pytest_plugin.py`) en `pytest_terminal_summary`.
- **B**: `e2e/main.py` construye el `Environment`/`Reporter` y corre los
  flows en proceso (como `api_e2e` hoy), sin pytest. Mas simple pero pierde
  el ecosistema pytest (markers, -k, fixtures, reporting). Solo si A da
  fricciones grandes con el container.

Preferir **A**: el usuario pidio "lo mas modularizado posible" y pytest es
el estandar Python para eso. El container corre `pytest` directo.

## B.5 — Container Docker `e2e`

NUEVO servicio + dockerfile, analogo al `feature` actual pero **Python**:

- `docker/dockerfiles/{local,dev,test}/e2e/Dockerfile`:
  - base Python 3.14 (o la imagen oficial de playwright-python que ya trae
    browsers + deps de sistema: `mcr.microsoft.com/playwright/python:vX`).
    EVALUAR usar la imagen oficial de playwright-python (trae chromium +
    webkit + firefox + deps de SO) vs instalar a mano. Preferir la oficial.
  - copia `devtools/` (para `.venv` + pyproject) + `tests/`.
  - `uv sync` del entorno + `playwright install` (si no usa la imagen oficial).
  - entrypoint que deja el container vivo (como `feature-entrypoint.sh`),
    crea sentinel `/tmp/.e2e-ready`.
- `docker/docker-compose/{local,dev,test}.yml`: agregar servicio `e2e`
  (profile `e2e`, `network_mode: host` o equivalente para alcanzar las URLs
  publicas dev/stage). Inyectar `AWS_PROFILE`/credenciales del host para SSM
  (montar `~/.aws` read-only o pasar las env vars temporales).
- El container NO necesita el stack de apps local (corre contra desplegado);
  solo necesita salida a internet + acceso a SSM/Neon.

`devtools/e2e/main.py` levanta el container con `docker compose --profile
e2e up -d e2e`, espera el sentinel, y corre `compose_exec(... pytest
tests/<module> ...)`. Reusa los helpers `shared.compose` de devtools.

> **Decision a confirmar en impl**: si la imagen oficial de
> playwright-python (Python 3.13-based) choca con el pin 3.14 del proyecto,
> usar imagen base 3.14 + `playwright install --with-deps`. Documentar la
> que quede. NO bloquear el plan por esto; es un detalle de la fase B.

## B.6 — Deps en `devtools/pyproject.toml`

Agregar a un grupo (ej. `[dependency-groups] e2e` o las deps de devtools):
`playwright`, `pytest`, `pytest-base-url` (opcional), `httpx`, `psycopg`,
`boto3`. Varias ya estan (boto3, psycopg, httpx para api_e2e). `uv lock` +
`uv sync`. Verificar con `python devtools/run.py upgrade_deps --dry-run`.

## Verificacion de la fase B

```bash
python devtools/run.py e2e --help            # describe() + flags
python devtools/run.py e2e --module=foo      # error de validacion (AC-5)
python devtools/run.py e2e --env=prod        # error: prod prohibido (AC-5)

# Build del container e2e
python devtools/run.py docker rebuild --env=local --target=e2e  # o compose build
docker compose -p portfolio -f docker/docker-compose/local.yml \
  --profile e2e up -d e2e
docker exec portfolio-e2e-local test -f /tmp/.e2e-ready && echo ready
docker exec portfolio-e2e-local devtools/.venv/bin/python -m pytest \
  tests/ --collect-only -q   # pytest descubre los tests
```

## Done de la fase B

- [ ] `devtools/e2e/{main,flags,README}.py` creados; `e2e --help` responde.
- [ ] Validacion de flags (module/env/samples) con errores claros.
- [ ] Container `e2e` buildea y queda ready (`/tmp/.e2e-ready`).
- [ ] `pytest tests/ --collect-only` descubre los tests desde el container.
- [ ] Deps E2E en `devtools/pyproject.toml` + `uv.lock` actualizado.
- [ ] `run.py` registra `e2e` (aparece en `python devtools/run.py` sin args).

[<- 03 fase shared](03-fase-shared.md) | [Siguiente: 05 modulo api ->](05-fase-modulo-api.md)
