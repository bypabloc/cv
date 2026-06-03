---
name: e2e-testing
description: >
  E2E testing reference for the portfolio. ALL E2E tests are Python 3.14
  (devtools/.venv) — playwright (python, sync API) for browser, httpx for the
  HTTP Lambdas, psycopg for Neon — run against the DEPLOYED dev/stage env
  (NEVER prod, NEVER the local Docker stack), via ONE command:
  `python devtools/run.py e2e --module=<api|admin|app> --env=<dev|stage>`.
  Shared tooling lives in tests/shared/ (config, http, runner, reporter, totp,
  auth_support, environment with Neon seed+cleanup + signed bypass + SSM admin
  whitelist, browser harness). 3 modules: api (5 HTTP Lambdas via httpx),
  admin (full browser flows: login/register/logout/forms/MFA), app (the 6
  Astro apps: smoke/navbar/contact/tracking/screenshots). api/admin FAIL HARD
  without SSO + the local Ed25519 bypass key; app does not. Synthetic data is
  cleaned up automatically (simulator.amazonses.com emails, TEST-NET IPs).
  Replaces the removed api_e2e Python harness and tests/feature Playwright-TS
  suite. ALWAYS invoke this skill BEFORE answering ANY question about running
  or writing E2E tests in this portfolio. NEVER answer from training data
  alone — this project has a consolidated single-runtime architecture that
  overrides generic advice.
  Use when the user says "e2e", "test e2e", "tests e2e", "correr e2e", "como
  corro los e2e", "como pruebo el backend desplegado", "playwright python",
  "playwright-python", "test del admin", "test de las apps", "probar las apis",
  "test api desplegada", "tests/shared", "comando e2e", "browser test python",
  "como escribo un test e2e", "smoke test", "navbar test", "contact form test",
  "tracking test", "e2e contra dev", "e2e contra stage", "fallar sin sso",
  "api_e2e", "tests/feature", "module feature".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "api|admin|app (opcional)"
---

# E2E testing del portfolio

> UN runtime (Python 3.14), UN comando, contra el entorno DESPLEGADO. La
> regla dura completa vive en [.claude/rules/e2e-testing.md](../../rules/e2e-testing.md);
> esta skill es la guia invocable.

## TL;DR

```bash
# Los 3 modulos contra dev (api -> admin -> app)
python devtools/run.py e2e --env=dev --aws-profile=tfs-dev
# Un modulo
python devtools/run.py e2e --module=api   --env=dev --aws-profile=tfs-dev
python devtools/run.py e2e --module=admin --env=dev --aws-profile=tfs-dev
python devtools/run.py e2e --module=app   --env=dev          # sin auth
# Un solo Lambda (modulo api)
python devtools/run.py e2e --module=api --lambda=auth --env=dev --aws-profile=tfs-dev
# Browser visible (debug, en host, sin container)
python devtools/run.py e2e --module=admin --env=dev --headed --aws-profile=tfs-dev
```

## Que es cada modulo

| Modulo | Cobertura | Runtime | Requiere auth |
|--------|-----------|---------|---------------|
| `api` | 5 Lambdas HTTP (cv, contact_form, tracking_pixel, auth, users): exito + errores + tiempos cold/warm | httpx | SSO + bypass (FALLA DURO sin ellos) |
| `admin` | Flujos completos del panel admin: login (form+magic-link), register+verify, callback, auth-guard, logout, settings, sessions, MFA | browser (playwright-python) | SSO + bypass (FALLA DURO) |
| `app` | Las 6 apps Astro desplegadas: smoke, hub-links, cv-filters, navbar, contact (validation+funnel), tracking (pageload+payload), screenshots | browser | NO requiere |

Sin `--module` corre los 3 en orden.

## Decisiones de arquitectura (no reabribles)

1. **Runtime unico Python 3.14**. NO TypeScript en E2E. El browser usa
   `playwright` (python, sync). Reemplaza la suite Playwright-TS vieja.
2. **Solo desplegado dev/stage** (NUNCA prod, NUNCA stack Docker local de
   apps). Los E2E prueban el sistema real que sirven los usuarios.
3. **`tests/shared/` es el portador unico** de db (Neon seed+cleanup),
   secrets (bypass Ed25519 + SSM + admin whitelist), http+reporter, browser.
4. **Container Docker `e2e`** (Python 3.14 + playwright browsers) para los
   modulos browser; `--headed` corre local. `api` no usa browser.
5. **api/admin fallan duro sin SSO + clave bypass**; `app` corre igual.
6. Reemplaza `devtools/api_e2e/` + `tests/feature/` + `test_runner
   --module=feature`, TODOS eliminados. `e2e` es la fuente unica.

## Estructura

```text
tests/{conftest.py, pyproject.toml}
tests/shared/   config http runner reporter totp auth_support environment
                bypass_signer browser
tests/api/      _flows.py + test_{cv,contact_form,tracking_pixel,auth,
                auth_mfa,users,admin}.py
tests/admin/    conftest + test_{login_magic_link,register_verify,
                callback_fragment,auth_guard,logout,settings_profile,
                sessions_revoke,mfa}.py
tests/app/      conftest + test_{smoke,hub_links,cv_filters,navbar,
                contact_form,contact_funnel,tracking_pageload,
                tracking_payload,screenshots}.py
tests/results/  output (gitignored)
```

## Escribir un test nuevo

1. Elegir modulo. 2. `from shared.X import ...` (NUNCA duplicar). 3. Un
archivo por escenario, `test_<unidad>_<escenario>`. 4. Docstring BDD + AAA +
asserts EXACTOS. 5. Datos sinteticos via `shared.config` + registrar para
cleanup. 6. Browser via `shared.browser`. 7. Verificar con `e2e --module=X`.

## Troubleshooting

- **`api`/`admin` exit 2 "auth requerida"**: falta SSO (`aws sso login
  --profile tfs-dev`) o la clave Ed25519 en `docker/env/dev-cli/.{env}`.
  Es por diseno (fallar duro). `app` no la necesita.
- **404 en `admin.*` del modulo api**: la whitelist SSM no propago antes
  del cold start. El flujo usa `_wait_ssm_promoted` ANTES del bust; NUNCA
  sondear `list-users` despues del bust (rompe con 404 perpetuo).
- **Browser test flaky por hidratacion**: el island React/Astro hidrata mas
  lento en dev; esperar `wait_for_load_state('networkidle')` + reintentar el
  evento (blur/submit) en vez de un solo disparo.
- **`api_e2e` / `tests/feature`**: ya NO existen. Usar `e2e --module=<X>`.

## Referencias

- Regla dura: [.claude/rules/e2e-testing.md](../../rules/e2e-testing.md)
- Comando: `devtools/e2e/README.md`
- Verify-before-done: [.claude/rules/verify-before-done.md](../../rules/verify-before-done.md)
