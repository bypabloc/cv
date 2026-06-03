# 02 — Arquitectura de tests (estructura + flujo de datos)

[<- 01 contexto](01-contexto-y-decision.md) | [Siguiente: 03 fase shared ->](03-fase-shared.md)

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
api_e2e (Python/HTTP)                 test_runner --module=feature (TS)
   |                                     |
   v                                     v
python run.py api_e2e --env=dev       run_feature() -> docker compose
   |                                     |  levanta container `feature`
   v                                     v  (chromium+webkit)
devtools/api_e2e/*.py                  ./node_modules/.bin/playwright test
 (flows + environment + reporter)        |
   |                                     v
   v                                  tests/feature/*.spec.ts (TS)
api.portfolio.dev (Lambdas HTTP)       -> nginx local :9970 (6 apps Astro)
```

### Despues

```text
                python run.py e2e --module=<api|admin|app> --env=dev
                                   |
                                   v
                          devtools/e2e/main.py
              (resuelve secretos via tests.shared; decide runner)
                /                  |                       \
        --module=api        --module=admin          --module=app
         (httpx puro)        (browser)               (browser)
              |                   |  levanta container `e2e`    |
              |                   |  (Python 3.14 + playwright)  |
              v                   v                              v
       pytest tests/api/    pytest tests/admin/          pytest tests/app/
              \                   |                              /
               \                  v                             /
                ----------> tests/shared/ <--------------------
               (db Neon | secrets bypass/SSM | http | browser | reporter)
                                   |
                                   v
              {api.,admin.,niche.}portfolio.dev.the-full-stack.com
                          (backend + apps DESPLEGADOS)
```

## 5. Diagrama ER

`N/A — no hay cambios en base de datos`. El plan no modela entidades nuevas;
reusa el schema Neon existente para seed/cleanup de datos sinteticos (ya
existente en `api_e2e/environment.py`).

## Estructura final de `tests/`

```text
tests/
├── conftest.py                  # pytest: --env, --aws-profile, --samples,
│                                #   --keep-data, --lambda; fixtures globales
├── pyproject.toml               # config pytest del arbol tests/ (markers,
│                                #   testpaths). Deps en devtools/pyproject.toml
├── README.md                    # como correr/escribir E2E (apunta a la rule)
├── shared/                      # HERRAMIENTAS COMPARTIDAS (Python)
│   ├── __init__.py
│   ├── config.py                # URLs/origins por env, IpRotator, emails
│   │                            #   sinteticos, NICHE, event_type_id (ex api_e2e/config)
│   ├── db.py                    # Neon via SSM: seed code/token hash,
│   │                            #   cleanup users/contacts/tracking (ex environment seed)
│   ├── secrets.py               # bypass Ed25519 firmado + SSM resolver +
│   │                            #   admin whitelist promote/restore (ex environment)
│   ├── http.py                  # HttpClient (httpx + timing, GET no-redirect),
│   │                            #   Response (ex support.py)
│   ├── reporter.py              # CaseResult + tabla de tiempos + veredicto
│   ├── runner.py                # Runner: N samples, clasifica PASS/FAIL,
│   │                            #   make_body (ex runner.py)
│   ├── totp.py                  # generador TOTP RFC 6238 (ex totp.py)
│   ├── auth_support.py          # helpers auth (register active, field,
│   │                            #   STRONG/WRONG_PASSWORD, FAKE_JWT) (ex _auth_support)
│   └── browser.py               # NUEVO: harness playwright-python
│                                #   (launch, page, goto, click, fill, login,
│                                #   logout, wait_selector, install_bypass,
│                                #   capture_track, disable_send_beacon, screenshot)
├── api/                         # MODULO api — Lambdas HTTP (httpx puro)
│   ├── __init__.py
│   ├── conftest.py              # fixtures del modulo (env, http, reporter)
│   ├── test_cv.py               # cv: 10 read actions + errores (ex flow_readonly)
│   ├── test_contact_form.py     # contact.create + errores (ex flow_readonly)
│   ├── test_tracking_pixel.py   # tracking.track + errores (ex flow_readonly)
│   ├── test_auth.py             # register/login/verify/session (ex flow_auth)
│   ├── test_auth_mfa.py         # MFA TOTP/email-code/recovery (ex flow_auth_mfa)
│   ├── test_users.py            # profile/status/change-email/delete (ex flow_users)
│   └── test_admin.py            # admin.* con promote/restore SSM (ex flow_admin)
├── admin/                       # MODULO admin — browser (flujos completos)
│   ├── __init__.py
│   ├── conftest.py              # fixtures browser (page, bypass instalado, seed)
│   ├── test_login_magic_link.py # login UI + magic-link real (seed Neon)
│   ├── test_register_verify.py  # register UI + verify-code real (seed Neon)
│   ├── test_callback_fragment.py# callback fragment hash (client-side)
│   ├── test_auth_guard.py       # AuthGuard redirect (sin sesion)
│   ├── test_logout.py           # logout (UI) + multi-tab + SPA fallback
│   ├── test_settings_profile.py # settings: update display_name (flujo real)
│   ├── test_sessions_revoke.py  # sessions-mgmt: list + revoke otra sesion
│   └── test_mfa.py              # MFA UI: setup TOTP + login 2FA (opcional fase)
├── app/                         # MODULO app — las 6 apps Astro (browser)
│   ├── __init__.py
│   ├── conftest.py              # fixtures browser (page, subdomain helper)
│   ├── test_smoke.py            # 6 subdominios + services responden 2xx
│   ├── test_hub_links.py        # hub cards -> hrefs env-driven (cross-subdomain)
│   ├── test_cv_filters.py       # filtros CV (?tech=) en 5 apps
│   ├── test_navbar.py           # navbar responsive (dropdown/drawer/breakpoint)
│   ├── test_contact_form.py     # form Zod validation + localStorage persist
│   ├── test_contact_funnel.py   # contact tracking (view + form_start)
│   ├── test_tracking_pageload.py# tracking always-on + SPA re-trigger
│   ├── test_tracking_payload.py # tracking payload schema (utm, viewport)
│   └── test_screenshots.py      # 3 viewports x 6 apps (PNG en tests/results/)
└── results/                     # output (PNG, json) — GITIGNORED
```

## Mapeo: viejo -> nuevo

| Origen (viejo) | Destino (nuevo) |
|----------------|-----------------|
| `devtools/api_e2e/config.py` | `tests/shared/config.py` |
| `devtools/api_e2e/environment.py` | `tests/shared/db.py` + `tests/shared/secrets.py` |
| `devtools/api_e2e/support.py` | `tests/shared/http.py` |
| `devtools/api_e2e/runner.py` | `tests/shared/runner.py` |
| `devtools/api_e2e/reporter.py` | `tests/shared/reporter.py` |
| `devtools/api_e2e/totp.py` | `tests/shared/totp.py` |
| `devtools/api_e2e/_auth_support.py` | `tests/shared/auth_support.py` |
| `devtools/api_e2e/flow_readonly.py` | `tests/api/test_{cv,contact_form,tracking_pixel}.py` |
| `devtools/api_e2e/flow_auth.py` | `tests/api/test_auth.py` |
| `devtools/api_e2e/flow_auth_mfa.py` | `tests/api/test_auth_mfa.py` |
| `devtools/api_e2e/flow_users.py` | `tests/api/test_users.py` |
| `devtools/api_e2e/flow_admin.py` | `tests/api/test_admin.py` |
| `devtools/api_e2e/main.py` + `flags.py` | `devtools/e2e/main.py` + `flags.py` |
| `tests/feature/fixtures/index.ts` | `tests/shared/browser.py` + `tests/shared/config.py` |
| `tests/feature/helpers/{screenshot,inspect-overlay}.ts` | `tests/shared/browser.py` |
| `tests/feature/admin/*.spec.ts` (7) | `tests/admin/test_*.py` |
| `tests/feature/{smoke,navbar,contact,tracking}/*.spec.ts` | `tests/app/test_*.py` |

## Patron pytest (cobertura == descriptiva)

Cada test es una funcion `def test_<unidad>_<escenario>()` con docstring
BDD (Given/When/Then) y cuerpo AAA. Los flujos largos de `api_e2e` (que hoy
son funciones imperativas que encadenan pasos) se portan como tests pytest
que comparten setup via fixtures de `conftest.py`. Asserts EXACTOS
(`== valor`, status codes exactos), nunca rangos.

## Conversion del modelo de ejecucion

- `api_e2e` hoy usa un `Runner` propio que corre N samples y clasifica
  PASS/FAIL imperativamente, con un `Reporter` de tiempos. Se CONSERVA ese
  `Runner`/`Reporter` (movidos a `tests/shared/`) para no perder el reporte
  de tiempos por caso (cold/warm por Lambda) — pero los flows pasan a ser
  funciones `test_*` orquestadas por pytest. El comando `e2e` invoca
  `pytest` y, al final, imprime el resumen de tiempos que el `Reporter`
  acumulo (via un plugin/fixture pytest que recolecta los `CaseResult`).
- Alternativa de menor riesgo (ver fase C): mantener el `Runner` imperativo
  y exponer cada flow como UN `test_*` que lo invoca, dejando que el
  `Reporter` siga siendo la fuente del resumen. Se decide en la fase C.

[<- 01 contexto](01-contexto-y-decision.md) | [Siguiente: 03 fase shared ->](03-fase-shared.md)
