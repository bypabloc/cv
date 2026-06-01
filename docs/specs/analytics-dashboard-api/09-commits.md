# 09 — Commits

[< 08-descomposicion-paralelizacion](08-descomposicion-paralelizacion.md) | [Siguiente: 10-paralelizacion-worktrees >](10-paralelizacion-worktrees.md)

> Lista de commits incrementales del plan. Cada commit es atomico,
> deja el repo verde, y se redacta en Conventional Commits espanol (ver
> [.claude/rules/git-workflow.md](../../.claude/rules/git-workflow.md)).
> Cada commit pasa SU verificacion ANTES de commitearse — la
> verificacion no se difiere al final.

## Branch

```bash
# Desde dev:
git checkout dev && git pull
git checkout -b feature/analytics-dashboard-api
```

NO se trabaja directo en `dev`/`stage`/`main` (rules protegen).

## Secuencia

### Commit 1 — Plan escrito

```text
docs(specs): agrega plan analytics-dashboard-api

- Define lambda nuevo `analytics` con GET /analytics, operations+actions, rate-limit 10/min/IP y cache 60s
- Documenta 22 criterios de aceptacion numerados, 19 actions distribuidos en 8 operations
- Detalla queries SQL por endpoint, capa de cache, testing por capa, archivos afectados (~190)
- Define descomposicion paralelizable en 7 worktrees + base secuencial de 7 tareas
- Incluye seccion de verificacion E2E (gate del PR) con bateria de comandos reales
```

Archivos:

- `docs/specs/analytics-dashboard-api/README.md`
- `docs/specs/analytics-dashboard-api/01-contexto-y-decision.md`
- `docs/specs/analytics-dashboard-api/02-arquitectura.md`
- ... (12 archivos de la spec)

Verify:

```bash
ls docs/specs/analytics-dashboard-api/ | wc -l   # == 12
markdownlint docs/specs/analytics-dashboard-api/*.md
```

---

### Commit 2 — (Condicional) Indices Neon

Solo si en B-2 detectamos indices faltantes. Si todos existen, este
commit no se hace.

```text
feat(db): agrega indices analytics para queries del dashboard

- Indices en vis_sessions (first_seen_at, last_seen_at, device_type, browser)
- Indices en vis_session_visits (started_at, session_id, country, niche, referrer)
- Indices en vis_tracking_events (session_id, event_type_id, page_path, niche)
- Indices en vis_contacts (created_at, status, niche)
- Migration Alembic forward-only; downgrade re-aplica DROP INDEX
```

Archivos:

- `serverless/lambda/shared/db/alembic/versions/<rev>_analytics_indexes.py`

Verify:

```bash
serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev
psql "$(grep -m1 '^DB_URL=' docker/env/server/.dev | cut -d= -f2-)" \
  -c "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND indexname LIKE 'idx_vis%';" | grep idx_vsv_started_at
```

---

### Commit 3 — Scaffold + manifest + pyproject

```text
feat(analytics): scaffold del lambda con manifest + pyproject

- Lambda `analytics` en serverless/lambda/services/analytics/
- GET /analytics, runtime python3.13 arm64, memory 512MB, timeout 30s
- SnapStart habilitado, neon-url secret, tablas cache + rate-limit-*
- pyproject sin deps de runtime (cierre transitivo de shared/)
- Env vars de defaults (paginacion, fechas, TTL cache)
```

Archivos:

- `serverless/lambda/services/analytics/manifest.yaml`
- `serverless/lambda/services/analytics/pyproject.toml`
- `serverless/lambda/services/analytics/.gitignore`
- `serverless/lambda/services/analytics/README.md`
- `serverless/lambda/services/analytics/core/__init__.py`

Verify:

```bash
cd serverless/lambda/services/analytics && uv sync && cd -
python devtools/run.py serverless lint-deps --lambda=analytics  # exit 0
```

---

### Commit 4 — Settings (config + operations)

```text
feat(analytics): registra OPERATIONS con 8 dominios y 19 actions

- ErrorCode enum con codes 0/1000-1003/4030-4290/5100/6000
- LogMetricType para metricas custom (Query{Ok,Rejected,Error}, Cache{Hit,Miss})
- OPERATIONS mapea cada (op, action) a su controller_module + class
```

Archivos:

- `core/settings/__init__.py`
- `core/settings/config.py`
- `core/settings/operations.py`

Verify:

```bash
python -c "from core.settings.operations import OPERATIONS; \
  assert set(OPERATIONS.keys()) == {'analytics','events','sessions','visits','geo','devices','funnel','contacts'}"
```

---

### Commit 5 — Handler + utils + modelos comunes

```text
feat(analytics): handler skeleton + rate_limit_guard + DateRange/Pagination

- Handler GET via shared.http.http_handler con event_model construido
- rate_limit_guard delega a shared.rate_limit con endpoint='/analytics'
- DateRange con defaults 30d, max 90d, error 1001 si span > 90d
- Pagination con page>=1, page_size 1-200, default 50
- _Meta (alias _meta) recibe ip/country/user_agent inyectados por http_handler
```

Archivos:

- `core/handler.py`
- `core/utils/__init__.py`
- `core/utils/rate_limit_guard.py`
- `core/models/__init__.py`
- `core/models/_common.py`

Verify:

```bash
python -m compileall -q serverless/lambda/services/analytics/core
```

(Tests aun no, se agregan en commit 6.)

---

### Commit 6 — Test infrastructure (conftest + helpers)

```text
test(analytics): conftest unit + integration + helpers

- conftest raiz con sys.path setup, env vars de runtime, fixtures
  mock_db_session, mock_check_or_raise, no_cache
- conftest integration con db_url fixture (lee solo la key) y
  namespace de cache aislado
- helpers para construir eventos GET y seedear data
- Tests de models comunes (DateRange + Pagination) verdes
```

Archivos:

- `tests/conftest.py`
- `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- `tests/unit/_helpers.py`
- `tests/integration/conftest.py`
- `tests/integration/_fixtures/__init__.py`
- `tests/integration/_fixtures/event_builder.py`
- `tests/integration/_fixtures/seed_data.py`
- `tests/unit/models/test__common/test_date_range_when_no_dates_then_defaults_30d.py`
- `tests/unit/models/test__common/test_date_range_when_range_over_90d_then_raises.py`
- `tests/unit/models/test__common/test_date_range_when_from_greater_than_to_then_raises.py`
- `tests/unit/models/test__common/test_pagination_when_page_size_over_max_then_raises.py`
- `tests/unit/models/test__common/test_pagination_when_page_zero_then_raises.py`
- `tests/unit/utils/test_rate_limit_guard_when_meta_none_then_uses_unknown.py`
- `tests/unit/utils/test_rate_limit_guard_when_blacklisted_then_raises.py`
- `tests/unit/utils/test_rate_limit_guard_when_rate_limited_then_raises.py`

Verify:

```bash
python devtools/run.py serverless tests --type=unit --lambda=analytics -- -k "_common or rate_limit_guard"
```

---

### Commit 7 — Lambda `db`: seed-rate-limit-rule command

```text
feat(db): agrega command seed-rate-limit-rule para insertar reglas

- Command parsea {rule_key, kind, limit, window_seconds, algorithm, description}
- PutItem con ConditionExpression: crea si no existe, sino actualiza
- Devuelve {action: created|updated, rule_key}
- Event JSON para insertar la rule /analytics 10 req/min/IP
- Tests unit: create + update + valor invalido + missing args
```

Archivos:

- `serverless/lambda/services/db/core/commands/seed_rate_limit_rule.py`
- `serverless/lambda/services/db/core/handler.py` (registrar command)
- `serverless/lambda/services/db/events/seed_rate_limit_analytics.json`
- `serverless/lambda/services/db/tests/unit/commands/test_seed_rate_limit_rule_when_new_then_creates.py`
- `serverless/lambda/services/db/tests/unit/commands/test_seed_rate_limit_rule_when_existing_then_updates.py`
- `serverless/lambda/services/db/tests/unit/commands/test_seed_rate_limit_rule_when_missing_args_then_raises.py`
- `serverless/lambda/services/db/tests/unit/commands/test_seed_rate_limit_rule_when_invalid_kind_then_raises.py`

Verify:

```bash
python devtools/run.py serverless tests --type=unit --lambda=db -- -k seed_rate_limit_rule
```

---

### Commits 8-14 — Operations (P-1..P-7 paralelizables)

Cada uno es UN commit por fase paralelizable. Pueden hacerse en
paralelo en worktrees distintos (ver [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md)).

#### Commit 8 — Operation `analytics` (P-1)

```text
feat(analytics): operation analytics con 7 actions y queries SQL

- Models: OverviewInput, TimeseriesInput, TopPagesInput, TopReferrersInput,
  TopNichesInput, ActiveNowInput, RetentionInput
- Service: overview (7 KPIs), timeseries (bucket day|hour|week),
  top-pages, top-referrers (+ UTM), top-niches, active-now (TTL 10s),
  retention (new vs returning)
- Controllers: 7 archivos, cada uno con guard + service + shape
- Events de ejemplo: 7 JSONs
- Tests unit: models + service + controllers + parametricos para edge cases
```

#### Commit 9 — Operation `events` (P-2)

```text
feat(analytics): operation events (distribution + list + heatmap)

- distribution: events agrupados por event_type_id con porcentaje
- list: paginado, filtros niche/event_type/session_id/page_path
- heatmap: dia_semana (ISO) x hora con count
- Cache 60s en distribution + heatmap; list sin cache
- Tests unit por accion incluyendo edge cases de paginacion
```

#### Commit 10 — Operation `sessions` (P-3)

```text
feat(analytics): operation sessions (list + detail)

- list: paginado con join a vis_session_visits para visits_count
- detail: 3 queries (session + visits + count events); 404 si no existe
- Filtros device_type/browser en list
- Tests unit + edge cases (session_id inexistente, sin visits)
```

#### Commit 11 — Operation `visits` (P-4)

```text
feat(analytics): operation visits (list + landing-pages)

- list: paginado con UTM, referrer, landing_page_path, niche, country
- landing-pages: ranking por visits agrupado por landing_page_path
- Cache 60s en landing-pages; list sin cache
- Tests unit por accion
```

#### Commit 12 — Operations geo + devices (P-5)

```text
feat(analytics): operations geo (by-country) y devices (breakdown)

- geo/by-country: count distinct session_id agrupado por country (ISO-2)
- devices/breakdown: 3 distribuciones simultaneas (device_type, browser, os)
- Cache 60s en ambos
- Tests unit
```

#### Commit 13 — Operation funnel (P-6)

```text
feat(analytics): operation funnel (conversion)

- CTE con counts de sessions / visits / contacts en el rango
- Calcula 3 rates (session_to_visit, visit_to_contact, session_to_contact)
- Manejo de division por cero en Python (no en SQL)
- Cache 60s
```

#### Commit 14 — Operation contacts (P-7)

```text
feat(analytics): operation contacts (list + by-status)

- list: paginado con filtros status/niche
- by-status: distribucion por status (new/contacted/qualified/converted/rejected)
- Cache 60s en by-status; list sin cache
- Tests unit
```

---

### Commit 15 — Tests integration (F-1)

```text
test(analytics): tests integration E2E contra dev DB

- test_overview_e2e_happy_path: GET overview con dates -> 200 + shape
- test_overview_e2e_range_too_wide: from/to > 90d -> 400 code 1001
- test_rate_limit_e2e_block_after_10_requests: 11va request -> 429
- test_sessions_detail_e2e_not_found: session_id inexistente -> 404
- test_cache_e2e_hit_returns_same_data: 2 requests identicas -> hit
- test_funnel_e2e_with_seeded_data: seed + GET funnel -> rates correctos
```

Archivos:

- `tests/integration/test_overview_e2e_happy_path.py`
- `tests/integration/test_overview_e2e_range_too_wide.py`
- `tests/integration/test_rate_limit_e2e_block_after_10_requests.py`
- `tests/integration/test_sessions_detail_e2e_not_found.py`
- `tests/integration/test_cache_e2e_hit_returns_same_data.py`
- `tests/integration/test_funnel_e2e_with_seeded_data.py`

Verify:

```bash
python devtools/run.py serverless tests --type=integration --lambda=analytics --aws-profile=tfs-dev
```

---

### Commit 16 — SnapStart runtime hooks (F-2)

```text
feat(analytics): runtime hooks SnapStart para acelerar cold start

- before_checkpoint: precalienta build_event_model y carga OPERATIONS
- after_restore: registra log marker (sin abrir conexion DB)
- Patron espejo de contact_form
```

Archivos:

- `core/runtime_hooks.py`

Verify:

```bash
python devtools/run.py serverless deploy --lambda=analytics --stage=dev --aws-profile=tfs-dev
# CloudWatch: aws logs tail /aws/lambda/portfolio-analytics-dev --follow
# Verificar Restore Duration < 1500ms en la metric REPORT
```

---

### Commit 17 — Promocion docs permanente + cleanup

```text
docs(serverless): agrega lambda analytics al knowledge tree y elimina spec efimera

- .claude/docs/serverless-backend/03-lambdas.md: agrega entrada de analytics
- docs/specs/analytics-dashboard-api/: eliminada (efimera, plan implementado)
```

Archivos:

- `.claude/docs/serverless-backend/03-lambdas.md` (modificar)
- `git rm -r docs/specs/analytics-dashboard-api/`

Este commit incluye la **verificacion E2E completa** (seccion 11):

- Bateria de curls contra dev (los 19 endpoints)
- Coverage gate verde
- Logs CloudWatch sin ERROR
- Rate-limit rule confirmada en DDB

Verify (ANTES de commit):

```bash
# Bateria completa — todo verde
python devtools/run.py serverless tests --type=unit --lambda=analytics
python devtools/run.py serverless tests --type=integration --lambda=analytics --aws-profile=tfs-dev
python devtools/run.py serverless tests --type=coverage --lambda=analytics  # >= 80% per-file
python devtools/run.py serverless lint-deps --lambda=analytics
# Smoke contra dev: usar los curls de la bateria B.1..B.6 en el archivo
# 11-verificacion-e2e.md (no hay smoke.sh dedicado, los `curl` inline son
# la fuente de verdad del test E2E manual).
```

---

## Resumen de secuencia

| Commit | Branch | Verde despues | Tests del scope |
|--------|--------|---------------|-----------------|
| 1 | feature/X | docs only | `markdownlint` |
| 2 (cond) | feature/X | + migration | `db migrate; \d` |
| 3 | feature/X | + scaffold | `lint-deps` |
| 4 | feature/X | + settings | `python -c "..."` |
| 5 | feature/X | + handler skel | `compileall` |
| 6 | feature/X | + test infra | unit `_common` + `rate_limit_guard` |
| 7 | feature/X | + db seeder | unit `db` seeder |
| 8 (P-1) | feature/X (o worktree) | + analytics op | unit analytics |
| 9 (P-2) | + worktree | + events op | unit events |
| 10 (P-3) | + worktree | + sessions op | unit sessions |
| 11 (P-4) | + worktree | + visits op | unit visits |
| 12 (P-5) | + worktree | + geo + devices | unit geo + devices |
| 13 (P-6) | + worktree | + funnel | unit funnel |
| 14 (P-7) | + worktree | + contacts | unit contacts |
| 15 | feature/X | + integration | integration 6 flujos |
| 16 | feature/X | + SnapStart | deploy dev + Restore < 1500ms |
| 17 | feature/X | + docs + cleanup | bateria E2E completa |

## PR

Un solo PR: `feature/analytics-dashboard-api -> dev`.

Body del PR (ver `git-workflow.md`, 4 secciones):

```markdown
## Problema
1. El backend persiste sessions/visits/events/contacts en Neon pero no hay forma de leerlos sin abrir `psql`.
2. El dashboard de analytics del portfolio necesita una API HTTP que exponga KPIs, timeseries, rankings y listados paginados.

## Solucion
1. Nuevo Lambda `analytics` (GET `/analytics?operation=...&action=...`) con 19 actions distribuidos en 8 operations.
2. Rate-limit 10 req/min/IP via `shared.rate_limit`, cache 60s via `shared.cache` en queries agregadas, SnapStart habilitado.

## Como probar
```bash
# Tests
python devtools/run.py serverless tests --type=unit --lambda=analytics
python devtools/run.py serverless tests --type=integration --lambda=analytics --aws-profile=tfs-dev
python devtools/run.py serverless tests --type=coverage --lambda=analytics  # >= 80% per-file
# Deploy dev
python devtools/run.py serverless deploy --lambda=analytics --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/seed_rate_limit_analytics.json --aws-profile=tfs-dev
# Smoke
curl "https://api.portfolio.dev.the-full-stack.com/analytics?operation=analytics&action=overview&from=2026-04-27&to=2026-05-27"
```

## TODO
- Auth real (Cloudflare Access o Bearer en SSM) — fuera de scope; se agregara cuando el dashboard frontend se exponga.
- Frontend Astro del dashboard — proxima iteracion.
```

[< 08-descomposicion-paralelizacion](08-descomposicion-paralelizacion.md) | [Siguiente: 10-paralelizacion-worktrees >](10-paralelizacion-worktrees.md)
