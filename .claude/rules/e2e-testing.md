# E2E testing del portfolio (comando `e2e`, Python unico)

> TODOS los tests E2E del portfolio son Python 3.14 (`devtools/.venv`),
> corren contra el entorno DESPLEGADO (dev/stage, NUNCA prod) via UN solo
> comando: `python devtools/run.py e2e --module=<api|admin|app>`. Las
> herramientas compartidas viven en `tests/shared/`. Reemplaza los dos
> sistemas viejos (el harness Python `api_e2e` + la suite Playwright
> TypeScript `tests/feature/`), AMBOS eliminados.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Cualquier archivo bajo `tests/` (`tests/shared/`, `tests/api/`,
  `tests/admin/`, `tests/app/`).
- El comando `devtools/e2e/` (orquestador).
- El container Docker `e2e` (`docker/dockerfiles/*/e2e/`).
- Escribir, correr o depurar cualquier test E2E del portfolio.

NO aplica a los unit tests (Vitest de apps/packages, pytest de devtools) ni
al backend serverless (esos tienen sus propios runners).

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** los E2E son Python 3.14 bajo `devtools/.venv`. Browser via
  `playwright` (python, sync API). API via `httpx`. Neon via `psycopg`.
  NUNCA TypeScript/Playwright-TS para E2E.
- **SIEMPRE** corren contra el entorno DESPLEGADO (dev o stage). NUNCA prod
  (mutan datos). NUNCA contra el stack Docker local de las apps (ese stack
  ya no participa de los E2E).
- **SIEMPRE** un solo comando:
  `python devtools/run.py e2e --module=<api|admin|app> --env=<dev|stage>`.
  Sin `--module` corre los 3 en orden (api -> admin -> app).
- **SIEMPRE** las herramientas compartidas viven en `tests/shared/`
  (config, http, runner, reporter, totp, auth_support, environment,
  browser). NUNCA duplicar bypass / seed Neon / datos sinteticos / harness
  de browser en un modulo: se importan de `shared`.
- **SIEMPRE** los tests importan `from shared.X import ...` (el
  `tests/pyproject.toml` declara `pythonpath = ['.']` con cwd `tests/`).
- **SIEMPRE** hermetico: ningun valor de secreto (bypass token, Neon URL,
  JWT) se imprime en stdout/stderr. Cumple `env-files.md`.
- **SIEMPRE** browser via el container Docker `e2e` (Python 3.14 +
  playwright browsers); el comando lo levanta on-demand para admin/app. Con
  `--headed` corre local en el host (debug). El modulo `api` no usa browser.
- **SIEMPRE** los modulos `api` y `admin` FALLAN DURO sin SSO + clave
  privada Ed25519 local (`docker/env/dev-cli/.{env}`): exit con error, NO
  skip silencioso. El modulo `app` NO requiere auth y corre igual.
- **SIEMPRE** los datos sinteticos creados (users/contacts/tracking/sessions)
  se limpian en el teardown del conftest del modulo (emails
  `@simulator.amazonses.com`, IPs TEST-NET RFC 5737), salvo `--keep-data`.
- **SIEMPRE** asserts EXACTOS (`== valor`, status codes exactos) + docstring
  BDD (Given/When/Then) + cuerpo AAA. Un archivo por escenario.
- **SIEMPRE** al promover un admin en la whitelist SSM (modulo api,
  `admin.*`), confirmar que SSM ya refleja el email (`_wait_ssm_promoted`)
  ANTES del `bust_users_cache`: `put_parameter` es eventualmente consistente
  y un cold start que lea SSM en la ventana cachea la whitelist VIEJA 300s
  -> 404 perpetuo. NUNCA sondear `admin.list-users` DESPUES del bust (crea
  contenedores nuevos durante la ventana del cold -> 404 perpetuo).
- **NUNCA** recrear `devtools/api_e2e/`, `tests/feature/` ni
  `test_runner --module=feature` (eliminados; `e2e` es la fuente unica).
- **NUNCA** correr `api`/`admin` contra prod ni en el CI de PR (mutan dev).
- **NUNCA** dejar que un test del modulo `app` MUTE el backend: los tests de
  tracking/funnel SIEMPRE interceptan `/track` con `page.route` (responden
  204 local), nunca dejan pasar el request real.

## Modulos

| Modulo | Que prueba | Runtime | Auth |
|--------|-----------|---------|------|
| `api` | Los 5 Lambdas HTTP (cv, contact_form, tracking_pixel, auth, users): exito + errores + tiempos | httpx puro | SSO + bypass (duro) |
| `admin` | Flujos completos del panel admin (login/verify/callback/auth-guard/logout/settings/sessions/MFA), 100% reales | browser | SSO + bypass (duro) |
| `app` | Las 6 apps Astro desplegadas: smoke, navbar, contact, tracking, screenshots | browser | no requiere |

## Estructura de `tests/`

```text
tests/
├── conftest.py              # pytest_addoption: --env --aws-profile --samples
│                            #   --keep-data --lambda + fixtures de sesion
├── pyproject.toml           # pytest config (pythonpath ['.'], markers)
├── shared/                  # PORTADOR UNICO de herramientas
│   ├── config.py            # URLs/origins por env, niche_origin, IpRotator,
│   │                        #   emails sinteticos
│   ├── http.py              # HttpClient (httpx + timing) + Response
│   ├── runner.py + reporter.py   # Runner (N samples) + reporte de tiempos
│   ├── totp.py              # TOTP RFC 6238 (stdlib)
│   ├── auth_support.py      # helpers auth (create active user, field, passwords)
│   ├── environment.py       # Neon seed/cleanup + bypass firmado + SSM +
│   │                        #   admin whitelist promote/restore (hermetico)
│   ├── bypass_signer.py     # firma Ed25519 del bypass (vendor, evita la
│   │                        #   colision de namespace con devtools/shared)
│   └── browser.py           # harness playwright-python (goto/click/fill/
│                            #   install_bypass/disable_send_beacon/capture_track)
├── api/                     # Lambdas HTTP (httpx) — _flows.py + test_*.py
├── admin/                   # browser, flujos completos — conftest + test_*.py
├── app/                     # browser, 6 apps — conftest + test_*.py
└── results/                 # output (PNG, json) — gitignored
```

## Como escribir un test nuevo

1. Elegir el modulo (`api` HTTP, `admin`/`app` browser).
2. Importar de `tests/shared` (NUNCA duplicar herramientas).
3. Un archivo por escenario; funcion `test_<unidad>_<escenario>`.
4. Docstring BDD (Given/When/Then) + cuerpo AAA. Asserts EXACTOS.
5. Datos sinteticos: emails de `shared.config.synthetic_email`, IPs del
   `IpRotator`; registrarlos en `created_emails`/`created_sessions` para el
   cleanup del conftest.
6. Browser: usar los helpers de `shared.browser` (no llamar playwright crudo).
7. Verificar con `python devtools/run.py e2e --module=<X> --env=dev`.

## Comando (referencia rapida)

```bash
# Los 3 modulos contra dev
python devtools/run.py e2e --env=dev --aws-profile=tfs-dev
# Un modulo
python devtools/run.py e2e --module=api   --env=dev --aws-profile=tfs-dev
python devtools/run.py e2e --module=admin --env=dev --aws-profile=tfs-dev
python devtools/run.py e2e --module=app   --env=dev   # sin auth
# Un solo Lambda del modulo api
python devtools/run.py e2e --module=api --lambda=auth --env=dev --aws-profile=tfs-dev
# Browser visible en host (debug)
python devtools/run.py e2e --module=admin --env=dev --headed --aws-profile=tfs-dev
# Conservar datos sinteticos (no limpiar Neon)
python devtools/run.py e2e --module=api --env=dev --keep-data --aws-profile=tfs-dev
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Escribir un E2E en TypeScript/Playwright-TS | El runtime unico es Python 3.14 | playwright-python en `tests/<module>/` |
| Correr E2E contra el stack Docker local | Los E2E prueban el sistema desplegado real | `--env=dev` o `--env=stage` |
| Correr `api`/`admin` contra prod | Mutan datos (users/contacts/tracking) | NUNCA prod; solo dev/stage |
| Duplicar bypass/seed/browser en un modulo | Rompe el portador unico | Importar de `tests/shared` |
| Imprimir el bypass token o la Neon URL | Leak de secreto | Hermetico: nunca a stdout |
| Sondear `admin.list-users` tras el bust | Crea contenedores nuevos en la ventana del cold -> 404 perpetuo | `_wait_ssm_promoted` ANTES del bust, nada despues |
| Skip silencioso de `api`/`admin` sin SSO | Oculta cobertura faltante | Fallar duro (exit error) |
| Dejar que un test `app` mute el backend | Contamina dev | Interceptar `/track` con `page.route` (204 local) |
| Recrear `api_e2e` / `tests/feature` / `--module=feature` | Eliminados; fuente unica es `e2e` | Usar `e2e --module=<X>` |
| Blur/submit sin esperar hidratacion del island | Handler React no montado -> error nunca aparece | `wait_for_load_state('networkidle')` + reintentar el evento |

## Referencias cruzadas

- Skill: [`/e2e-testing`](../skills/e2e-testing/SKILL.md) — guia invocable.
- `devtools/e2e/README.md` — referencia del comando (flags, container).
- [.claude/rules/python.md](python.md) — Python 3.14, ruff, testing.
- [.claude/rules/devtools.md](devtools.md) — convenciones de scripts.
- [.claude/rules/env-files.md](env-files.md) — NUNCA leer `.env` completos.
- [.claude/rules/auth-system.md](auth-system.md) — el dominio auth que el
  modulo api/admin ejercita.
- [.claude/rules/serverless-secrets.md](serverless-secrets.md) — SSM/KMS.
- [.claude/rules/verify-before-done.md](verify-before-done.md) — la bateria.
