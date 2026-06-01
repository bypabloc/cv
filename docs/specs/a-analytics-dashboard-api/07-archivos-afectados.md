# 07 — Archivos afectados

[< 06-testing](06-testing.md) | [Siguiente: 08-descomposicion-paralelizacion >](08-descomposicion-paralelizacion.md)

> Listado completo de archivos creados/modificados con su verificacion
> ejecutable. Convierte la lista en un checklist accionable.

## Crear

### Documentacion del plan (efimero — se elimina al mergear)

- `docs/specs/a-analytics-dashboard-api/README.md`
  - Verificar: `markdownlint docs/specs/a-analytics-dashboard-api/*.md` (warnings ok, errors no)
- `docs/specs/a-analytics-dashboard-api/01-contexto-y-decision.md` — idem
- `docs/specs/a-analytics-dashboard-api/02-arquitectura.md` — idem
- `docs/specs/a-analytics-dashboard-api/03-infraestructura.md` — idem
- `docs/specs/a-analytics-dashboard-api/04-queries-sql.md` — idem
- `docs/specs/a-analytics-dashboard-api/05-cache-layer.md` — idem
- `docs/specs/a-analytics-dashboard-api/06-testing.md` — idem
- `docs/specs/a-analytics-dashboard-api/07-archivos-afectados.md` — este archivo
- `docs/specs/a-analytics-dashboard-api/08-descomposicion-paralelizacion.md`
- `docs/specs/a-analytics-dashboard-api/09-commits.md`
- `docs/specs/a-analytics-dashboard-api/10-paralelizacion-worktrees.md`
- `docs/specs/a-analytics-dashboard-api/11-verificacion-e2e.md`

### Lambda nuevo — Infraestructura (Fase 1)

- `serverless/lambda/services/analytics/manifest.yaml`
  - Verificar: `python devtools/run.py serverless lint-deps --lambda=analytics` exit 0
  - Verificar: `python devtools/run.py serverless status --lambda=analytics --stage=local` no error
- `serverless/lambda/services/analytics/pyproject.toml`
  - Verificar: `cd serverless/lambda/services/analytics && uv sync` exit 0
- `serverless/lambda/services/analytics/.gitignore`
  - Excluye `build/`, `build.zip`, `.venv/`, `__pycache__/`, `*.pyc`
- `serverless/lambda/services/analytics/README.md`
  - Corto, linkea a `docs/specs/a-analytics-dashboard-api/`

### Lambda nuevo — Settings (Fase 1)

- `serverless/lambda/services/analytics/core/__init__.py` (vacio)
- `serverless/lambda/services/analytics/core/settings/__init__.py` (vacio)
- `serverless/lambda/services/analytics/core/settings/config.py`
  - Verificar: `python -m compileall -q core/settings/config.py`
- `serverless/lambda/services/analytics/core/settings/operations.py`
  - Verificar: `python -c "from core.settings.operations import OPERATIONS; assert 'analytics' in OPERATIONS"`

### Lambda nuevo — Models (Fase 2)

- `serverless/lambda/services/analytics/core/models/__init__.py` (vacio)
- `serverless/lambda/services/analytics/core/models/_common.py`
  - Verificar: `pytest tests/unit/models/test__common*.py -v`
- `serverless/lambda/services/analytics/core/models/analytics.py`
  - Verificar: `pytest tests/unit/models/test_overview_*.py tests/unit/models/test_timeseries_*.py ... -v`
- `serverless/lambda/services/analytics/core/models/events.py`
- `serverless/lambda/services/analytics/core/models/sessions.py`
- `serverless/lambda/services/analytics/core/models/visits.py`
- `serverless/lambda/services/analytics/core/models/geo.py`
- `serverless/lambda/services/analytics/core/models/devices.py`
- `serverless/lambda/services/analytics/core/models/funnel.py`
- `serverless/lambda/services/analytics/core/models/contacts.py`

### Lambda nuevo — Handler + Utils (Fase 1-2)

- `serverless/lambda/services/analytics/core/handler.py`
  - Verificar: `python -m compileall -q core/handler.py`
  - Verificar: `pytest tests/unit/handler/ -v`
- `serverless/lambda/services/analytics/core/utils/__init__.py` (vacio)
- `serverless/lambda/services/analytics/core/utils/rate_limit_guard.py`
  - Verificar: `pytest tests/unit/utils/test_rate_limit_guard*.py -v`
- `serverless/lambda/services/analytics/core/runtime_hooks.py` (Fase 10, SnapStart)

### Lambda nuevo — Controllers (Fases 3-7)

#### Operation `analytics`

- `core/controllers/__init__.py` (vacio)
- `core/controllers/analytics/__init__.py` (vacio)
- `core/controllers/analytics/overview.py`
- `core/controllers/analytics/timeseries.py`
- `core/controllers/analytics/top_pages.py`
- `core/controllers/analytics/top_referrers.py`
- `core/controllers/analytics/top_niches.py`
- `core/controllers/analytics/active_now.py`
- `core/controllers/analytics/retention.py`

#### Operation `events`

- `core/controllers/events/__init__.py` (vacio)
- `core/controllers/events/distribution.py`
- `core/controllers/events/list.py`
- `core/controllers/events/heatmap.py`

#### Operation `sessions`

- `core/controllers/sessions/__init__.py` (vacio)
- `core/controllers/sessions/list.py`
- `core/controllers/sessions/detail.py`

#### Operation `visits`

- `core/controllers/visits/__init__.py` (vacio)
- `core/controllers/visits/list.py`
- `core/controllers/visits/landing_pages.py`

#### Operation `geo`

- `core/controllers/geo/__init__.py` (vacio)
- `core/controllers/geo/by_country.py`

#### Operation `devices`

- `core/controllers/devices/__init__.py` (vacio)
- `core/controllers/devices/breakdown.py`

#### Operation `funnel`

- `core/controllers/funnel/__init__.py` (vacio)
- `core/controllers/funnel/conversion.py`

#### Operation `contacts`

- `core/controllers/contacts/__init__.py` (vacio)
- `core/controllers/contacts/list.py`
- `core/controllers/contacts/by_status.py`

Verificacion por controller (mismo patron):

- `python -m compileall -q core/controllers/<dominio>/<action>.py`
- `pytest tests/unit/controllers/<dominio>/test_<action>_*.py -v`

### Lambda nuevo — Services (Fases 3-7)

- `core/services/__init__.py` (vacio)
- `core/services/analytics_service.py` (Fase 3)
  - Verificar: `pytest tests/unit/services/test_analytics_*.py -v`
- `core/services/events_service.py` (Fase 4)
- `core/services/sessions_service.py` (Fase 5)
- `core/services/visits_service.py` (Fase 5)
- `core/services/geo_service.py` (Fase 6)
- `core/services/devices_service.py` (Fase 6)
- `core/services/funnel_service.py` (Fase 7)
- `core/services/contacts_service.py` (Fase 7)

### Lambda nuevo — Events de ejemplo

- `serverless/lambda/services/analytics/events/overview.json`
- `serverless/lambda/services/analytics/events/timeseries.json`
- `serverless/lambda/services/analytics/events/top_pages.json`
- `serverless/lambda/services/analytics/events/top_referrers.json`
- `serverless/lambda/services/analytics/events/top_niches.json`
- `serverless/lambda/services/analytics/events/active_now.json`
- `serverless/lambda/services/analytics/events/retention.json`
- `serverless/lambda/services/analytics/events/events_distribution.json`
- `serverless/lambda/services/analytics/events/events_list.json`
- `serverless/lambda/services/analytics/events/events_heatmap.json`
- `serverless/lambda/services/analytics/events/sessions_list.json`
- `serverless/lambda/services/analytics/events/sessions_detail.json`
- `serverless/lambda/services/analytics/events/visits_list.json`
- `serverless/lambda/services/analytics/events/visits_landing_pages.json`
- `serverless/lambda/services/analytics/events/geo_by_country.json`
- `serverless/lambda/services/analytics/events/devices_breakdown.json`
- `serverless/lambda/services/analytics/events/funnel_conversion.json`
- `serverless/lambda/services/analytics/events/contacts_list.json`
- `serverless/lambda/services/analytics/events/contacts_by_status.json`

Verificacion: cada JSON parseable con `python -m json.tool < events/<X>.json`.

### Tests del Lambda

#### Unit — models (~40 archivos)

`tests/unit/models/test_<input>_<escenario>.py` (uno por accion + uno
por escenario):

- `test__common/test_date_range_when_no_dates_then_defaults_30d.py`
- `test__common/test_date_range_when_range_over_90d_then_raises.py`
- `test__common/test_date_range_when_from_greater_than_to_then_raises.py`
- `test__common/test_pagination_when_page_size_over_max_then_raises.py`
- `test__common/test_pagination_when_page_zero_then_raises.py`
- `test_analytics/test_overview_input_when_valid_then_parses.py`
- `test_analytics/test_timeseries_input_when_invalid_bucket_then_raises.py`
- ... 1 archivo por escenario significativo (~30 archivos)

#### Unit — services (~30 archivos)

`tests/unit/services/test_<service>_<action>_<escenario>.py`:

- `test_analytics_overview_when_data_then_returns_shape.py`
- `test_analytics_overview_when_empty_db_then_zeros.py`
- `test_analytics_overview_when_visits_zero_then_bounce_rate_zero.py`
- ... etc

#### Unit — controllers (~25 archivos)

- `test_overview_controller_when_valid_then_calls_service.py`
- `test_overview_controller_when_blacklisted_then_raises.py`
- `test_overview_controller_when_rate_limited_then_raises.py`
- ... etc

#### Unit — handler (~5 archivos)

- `test_handler_when_known_op_then_dispatches.py`
- `test_handler_when_unknown_op_then_400.py`
- `test_handler_when_unknown_action_then_400.py`
- `test_handler_when_get_then_extracts_query_params.py`

#### Unit — utils (~3 archivos)

- `test_rate_limit_guard_when_meta_none_then_uses_unknown.py`
- `test_rate_limit_guard_when_blacklisted_then_raises.py`
- `test_rate_limit_guard_when_rate_limited_then_raises.py`

#### Integration (~6 archivos)

- `tests/integration/test_overview_e2e_happy_path.py`
- `tests/integration/test_overview_e2e_range_too_wide.py`
- `tests/integration/test_rate_limit_e2e_block_after_10_requests.py`
- `tests/integration/test_sessions_detail_e2e_not_found.py`
- `tests/integration/test_cache_e2e_hit_returns_same_data.py`
- `tests/integration/test_funnel_e2e_with_seeded_data.py`

#### Tests helpers

- `tests/conftest.py`
- `tests/unit/_helpers.py`
- `tests/integration/conftest.py`
- `tests/integration/_fixtures/__init__.py`
- `tests/integration/_fixtures/event_builder.py`
- `tests/integration/_fixtures/seed_data.py`

## Modificar

### Lambda `db` — agregar command `seed-rate-limit-rule`

- `serverless/lambda/services/db/core/commands/seed_rate_limit_rule.py` (NUEVO)
  - Verificar: `pytest serverless/lambda/services/db/tests/unit/commands/test_seed_rate_limit_rule.py -v`
- `serverless/lambda/services/db/core/handler.py` (registrar el command)
  - Verificar: `pytest serverless/lambda/services/db/tests/unit/handler/ -v`
- `serverless/lambda/services/db/events/seed_rate_limit_analytics.json` (NUEVO event)
  - Verificar: `python -m json.tool < events/seed_rate_limit_analytics.json`
- `serverless/lambda/services/db/manifest.yaml`
  - Solo si el command necesita un table nuevo en `uses`; en este caso `rate-limit-rules: read-write` ya esta (o se agrega).

### CI/CD

- `.github/workflows/deploy-backend.yml` — **NO se modifica** (auto-detect del nuevo Lambda).
- `.github/workflows/ci.yml` — **NO se modifica**.

### Documentacion permanente

Promocion de aprendizajes de la spec (al cerrar el plan):

- `.claude/docs/serverless-backend/03-lambdas.md`
  - Agregar entrada de `analytics` en la tabla de Lambdas (ya hay 6,
    sumar la 7ma).
  - Verificar: `markdownlint .claude/docs/serverless-backend/03-lambdas.md`
- `CLAUDE.md` (root)
  - En la tabla "Arbol de conocimiento" sumar referencia al Lambda
    nuevo si aporta valor (probablemente NO, ya cae bajo
    `serverless-backend`).

## Eliminar

- `docs/specs/a-analytics-dashboard-api/` — al cerrar el PR `feature/X ->
  dev`. Ultimo commit del plan: `git rm -r
  docs/specs/a-analytics-dashboard-api/`.
  - Verificar: `test ! -d docs/specs/a-analytics-dashboard-api`

## Resumen cuantitativo

| Categoria | Archivos |
|-----------|----------|
| Spec docs (efimero) | 12 |
| Lambda config (manifest, pyproject, .gitignore, README) | 4 |
| Lambda settings (config, operations) | 2 |
| Lambda models (_common + 8 dominios) | 9 |
| Lambda controllers (19 actions) | 19 |
| Lambda services (8 dominios) | 8 |
| Lambda handler + utils | 3 |
| Lambda runtime_hooks (SnapStart) | 1 |
| Lambda events de ejemplo | 19 |
| Unit tests (models + services + controllers + handler + utils) | ~100 |
| Integration tests | 6 |
| Tests fixtures + conftest | 6 |
| Lambda `db` mods (command + event) | 3 |
| Docs permanente (knowledge tree) | 1-2 |
| **Total approx** | **~190 archivos** |

[< 06-testing](06-testing.md) | [Siguiente: 08-descomposicion-paralelizacion >](08-descomposicion-paralelizacion.md)
