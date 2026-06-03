# 11 — Seccion 7: Archivos afectados

[<- 10 tests requeridos](10-tests-requeridos.md) | [Siguiente: 12 descomposicion ->](12-descomposicion-paralelizacion.md)

> Paths relativos desde root. Verificacion explicita por archivo (comando o
> criterio observable). Usar `devtools/.venv/bin/python` para compileall.

## Crear

### tests/shared/ (fase A)
- `tests/shared/__init__.py` — docstring-only
  - Verificar: import OK bajo `.venv`
- `tests/shared/config.py` — URLs/origins por env + IpRotator + emails + niches desplegados
  - Verificar: `test_config.py` PASS (subdomain + synthetic_email)
- `tests/shared/db.py` — Neon seed + cleanup (split de environment.py)
  - Verificar: import OK; hermetismo (sin Neon URL a stdout)
- `tests/shared/secrets.py` — bypass Ed25519 + SSM + admin whitelist
  - Verificar: `test_secrets_hermetic.py` PASS (canary)
- `tests/shared/http.py` — HttpClient + Response (ex support.py)
  - Verificar: import OK
- `tests/shared/runner.py`, `reporter.py`, `totp.py`, `auth_support.py` — ex api_e2e
  - Verificar: `test_runner.py` + `test_reporter.py` + `test_totp.py` PASS
- `tests/shared/browser.py` — harness playwright-python (NUEVO)
  - Verificar: import OK; `playwright` instalado en `.venv`
- `tests/conftest.py`, `tests/pyproject.toml`, `tests/README.md`
  - Verificar: `pytest tests/ --collect-only` OK
- `tests/results/.gitkeep`
  - Verificar: `tests/results/` en `.gitignore`

### devtools/e2e/ (fase B)
- `devtools/e2e/{__init__,main,flags}.py` + `pytest_plugin.py` + `README.md`
  - Verificar: `python devtools/run.py e2e --help` responde; `--module=foo` error
- `docker/dockerfiles/{local,dev,test}/e2e/Dockerfile`
  - Verificar: build OK; container queda ready (`/tmp/.e2e-ready`)
- `docker/scripts/e2e-entrypoint.sh`
  - Verificar: `bash -n e2e-entrypoint.sh`

### tests/api/ (fase C)
- `tests/api/{__init__,conftest}.py` + `test_{cv,contact_form,tracking_pixel,auth,auth_mfa,users,admin}.py`
  - Verificar: `e2e --module=api --env=dev` PASS (== cobertura api_e2e)

### tests/admin/ (fase D)
- `tests/admin/{__init__,conftest}.py` + `test_{login_magic_link,register_verify,callback_fragment,auth_guard,logout,settings_profile,sessions_revoke,mfa}.py`
  - Verificar: `e2e --module=admin --env=dev` PASS

### tests/app/ (fase E)
- `tests/app/{__init__,conftest}.py` + `test_{smoke,hub_links,cv_filters,navbar,contact_form,contact_funnel,tracking_pageload,tracking_payload,screenshots}.py`
  - Verificar: `e2e --module=app --env=dev` PASS; PNG en tests/results/

### Unit tests del comando (fase A/B/C)
- `devtools/tests/unit/src/e2e/test_{flags,describe}.py`
- `devtools/tests/unit/src/e2e_shared/test_{config,reporter,runner,totp,secrets_hermetic}.py`
  - Verificar: `test_runner --module=devtools --type=unit` verde, coverage >=80%

### Docs Claude (fase G)
- `.claude/rules/e2e-testing.md`
  - Verificar: existe + coherente con la arquitectura
- `.claude/skills/e2e-testing/SKILL.md`
  - Verificar: `claude -p` 5/5 angulos (claude-config-testing.md)

## Modificar

- `devtools/pyproject.toml` + `devtools/uv.lock` — deps E2E (playwright, pytest)
  - Verificar: `uv sync` OK; `playwright` importable
- `.gitignore` — agregar `tests/results/`, `tests/**/__pycache__/`
  - Verificar: `git status` no lista PNG
- `devtools/test_runner/flags.py` — quitar `feature`, rechazar con migracion
  - Verificar: `test_runner --module=feature` error con mensaje
- `devtools/test_runner/full_suites.py` — quitar branch feature + import
  - Verificar: `test_runner --module=devtools --type=unit` verde
- `devtools/test_runner/README.md` — quitar doc de feature
- `devtools/tests/unit/src/test_runner/flags.py` — actualizar asserts de feature
  - Verificar: pytest del modulo verde
- `docker/docker-compose/{local,dev,test,prod}.yml` — quitar servicio `feature`, agregar `e2e`
  - Verificar: `docker compose config` OK
- `.git-hooks/pre-push` — `step_feature_tests` -> `step_e2e` (politica de skip)
  - Verificar: pre-push corre (o saltea) sin romper
- `.git-hooks/config.json` — `feature_tests` -> `e2e_tests`
  - Verificar: JSON valido
- `.github/workflows/ci.yml` (+ posible workflow e2e dedicado) — revisar job feature/e2e
  - Verificar: CI verde en el PR
- `CLAUDE.md` — comandos `e2e`, estructura `tests/{api,admin,app,shared}/`, skills/rules index
  - Verificar: coherencia; sin `api_e2e`/`feature` como comando activo
- `packages/ui/src/components/ContactFormReact.tsx` — revisar referencia `api-e2e` del header bypass
  - Verificar: si el header no cambia, dejar y anotar; si cambia, actualizar
- `serverless/lambda/shared/crypto/{ed25519,bypass_token}.py` — menciones `api_e2e` -> `e2e`
  - Verificar: docstrings actualizados; tests del shared serverless verdes
- `devtools/bypass_token/README.md`, `devtools/weak_assertion/README.md` — menciones
  - Verificar: coherencia

## Eliminar (fase F)

- `devtools/api_e2e/` (16 archivos)
  - Verificar: `python devtools/run.py | rg -q api_e2e` -> sin match
- `devtools/tests/unit/src/api_e2e/` (4 archivos) — tras migrar a `e2e_shared/`
- `tests/feature/` (11 specs + config + helpers + fixtures)
  - Verificar: `rg -l "tests/feature"` sin hits funcionales
- `devtools/test_runner/feature.py`
- `docker/dockerfiles/{local,test}/feature/Dockerfile`
- `docker/scripts/feature-entrypoint.sh`
  - Verificar: `docker compose config` sin servicio feature

[<- 10 tests requeridos](10-tests-requeridos.md) | [Siguiente: 12 descomposicion ->](12-descomposicion-paralelizacion.md)
