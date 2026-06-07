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
git checkout -b feature/b-analytics-api
```

NO se trabaja directo en `dev`/`stage`/`main` (rules protegen).

> Plan FULL-STACK: los commits 1-17 son el track **backend** (Lambda
> `analytics`); los commits 18-24 son el track **frontend** (UI de
> metricas en `admin/`). Un solo PR `feature/b-analytics-api -> dev`
> cubre ambos. El git rm final de la spec va en el ultimo commit (24).

## Secuencia

### Commit 1 — Plan escrito

```text
docs(specs): agrega plan b-analytics-api (full-stack)

- Define lambda nuevo `analytics` con GET /analytics + auth JWT, operations+actions, rate-limit 10/min/IP y cache 60s
- Documenta 25 criterios de aceptacion numerados, 19 actions distribuidos en 8 operations
- Agrega la capa de UI de metricas (features Next.js en admin/) que consume el Lambda con Authorization Bearer
- Detalla queries SQL por endpoint, capa de cache, testing por capa, archivos afectados (~313)
- Define descomposicion paralelizable: track backend (7 worktrees) + track frontend (7 worktrees)
- Incluye seccion de verificacion E2E (gate del PR) con bateria de comandos reales + UI
```

Archivos:

- `docs/specs/b-analytics-api/README.md`
- `docs/specs/b-analytics-api/01-contexto-y-decision.md`
- `docs/specs/b-analytics-api/02-arquitectura.md`
- ... (12 archivos de la spec)

Verify:

```bash
ls docs/specs/b-analytics-api/ | wc -l   # == 12
markdownlint docs/specs/b-analytics-api/*.md
```

---

### Commit 2 — (Condicional) Indices Neon

Solo si en B-2 detectamos indices faltantes. Si todos existen, este
commit no se hace.

```text
feat(db): agrega indices analytics para queries de metricas

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

### Commit 5 — Handler + utils + auth + modelos comunes

```text
feat(analytics): handler skeleton + jwt_service + auth_guard + rate_limit_guard + DateRange/Pagination

- Handler GET via shared.lambda_kit.http_dispatch.http_handler con event_model construido
- core/services/jwt_service.py portado de services/users (require_active_user recibe Authorization header completo)
- core/utils/auth_guard.py llama require_active_user(data._meta.authorization); 401 code 4010 si falla
- rate_limit_guard delega a shared.rate_limit con endpoint='/analytics'
- DateRange con defaults 30d, max 90d, error 1001 si span > 90d
- Pagination con page>=1, page_size 1-200, default 50
- _Meta (alias _meta) declara authorization: str | None = Field(default=None, alias='authorization')
  con populate_by_name=True; recibe ip/country/user_agent/authorization inyectados por http_dispatch
```

Archivos:

- `core/handler.py`
- `core/services/__init__.py`
- `core/services/jwt_service.py`
- `core/utils/__init__.py`
- `core/utils/auth_guard.py`
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

### Commit 7 — Tests unit del auth_guard + jwt_service

```text
test(analytics): tests unit de jwt_service + auth_guard

- test_auth_guard_when_no_authorization_then_401
- test_auth_guard_when_invalid_jwt_then_401
- test_auth_guard_when_valid_jwt_then_returns_user
- test_auth_guard_when_disabled_user_then_403
- test_jwt_service_require_active_user_reads_authorization_header
```

> El seed de la rate-limit rule NO es un commit: se hace con el CLI
> ya existente al desplegar:
> `python devtools/run.py serverless rate-limit set --endpoint=/analytics --limit=10 --window=60 --stage=dev`
> (idem stage/prod). No se crea ningun command en el Lambda `db`.

Archivos:

- `tests/unit/utils/test_auth_guard_when_no_authorization_then_401.py`
- `tests/unit/utils/test_auth_guard_when_invalid_jwt_then_401.py`
- `tests/unit/utils/test_auth_guard_when_valid_jwt_then_returns_user.py`
- `tests/unit/utils/test_auth_guard_when_disabled_user_then_403.py`
- `tests/unit/services/test_jwt_service_require_active_user_reads_authorization_header.py`

Verify:

```bash
python devtools/run.py serverless tests --type=unit --lambda=analytics -- -k "auth_guard or jwt_service"
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

### Commit 16 — SnapStart con warm_db en el INIT (F-2)

```text
feat(analytics): SnapStart con warm_db en el INIT del handler

- snap_start: true en manifest.yaml (booleano; el alias :live lo gestiona el provisioner)
- handler.py importa modulos de modelos visitor concretos en el module-scope
- warm_db() en el INIT precalienta engine NullPool + configure_mappers (best-effort)
- Patron identico a contact_form y cv
```

Archivos:

- `serverless/lambda/services/analytics/manifest.yaml` (actualizar snap_start)
- `core/handler.py` (agregar imports de modelos + warm_db() en module-scope)

Verify:

```bash
python devtools/run.py serverless deploy --lambda=analytics --stage=dev --aws-profile=tfs-dev
# CloudWatch: aws logs tail /aws/lambda/portfolio-analytics-dev --follow
# Verificar Restore Duration < 1500ms en la metric REPORT
```

---

### Commit 17 — Promocion docs permanente del backend

```text
docs(serverless): agrega lambda analytics al knowledge tree

- .claude/docs/serverless-backend/03-lambdas.md: agrega entrada de analytics (7ma Lambda)
```

Archivos:

- `.claude/docs/serverless-backend/03-lambdas.md` (modificar)

Verify:

```bash
markdownlint .claude/docs/serverless-backend/03-lambdas.md
```

(El `git rm` de la spec NO va aqui: va en el ultimo commit, 24, tras la
UI.)

---

### Commits 18-23 — UI de metricas (track frontend, U-0..U-7)

Cada commit AGREGA features de metricas a la app `admin/` (package
`@portfolio/admin`) que entrego el plan `a-admin`. Las features NO se
empiezan hasta que `a-admin` este mergeado (shell + `api-client` +
`useAuthStore`). U-1..U-7 pueden hacerse en worktrees distintos
(ver [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md)).
Cada hook corre contra MSW hasta que el Lambda este vivo en el env.

#### Commit 18 — Query-keys raiz + MSW de metricas (U-0)

```text
feat(admin): query-keys raiz de metricas + handlers MSW de los 19 endpoints

- metrics-query-keys.ts: namespace ['metrics', ...] para todas las features
- handlers MSW de GET /analytics?operation=...&action=... (19 endpoints)
- Registrados en el handlers.ts raiz del admin (de a-admin)
```

Archivos:

- `admin/src/lib/metrics-query-keys.ts`
- `admin/src/mocks/handlers/metrics.ts`

Verify:

```bash
pnpm --filter @portfolio/admin test -- src/mocks
```

#### Commit 19 — Feature `analytics` (U-1)

```text
feat(admin): feature analytics (overview, timeseries, top-*, active-now, retention)

- Hooks Tanstack Query con Authorization Bearer via api-client (staleTime por endpoint)
- Componentes Recharts (timeseries, top-niches, retention) + DataTable (top-pages/referrers)
- Pages /metrics (overview + active-now) y /metrics/timeseries en el route group (admin)/
- Tests unit (hooks + componentes) contra MSW, coverage >= 80%
```

Archivos: `admin/src/features/analytics/**`,
`admin/src/app/(admin)/metrics/**`, tests mirror.

#### Commit 20 — Feature `sessions` de tracking (U-2)

```text
feat(admin): feature sessions de tracking (list + detail)

- list: DataTable + Tanstack Virtual (lista grande de sesiones de visitantes)
- detail: panel con session + visits + events_count; ruta /sessions/[id]
- NO confundir con sessions-mgmt (auth) del plan a-admin
- Tests unit contra MSW
```

Archivos: `admin/src/features/sessions/**`,
`admin/src/app/(admin)/sessions/**`, tests mirror.

#### Commit 21 — Features `events` + `visits` (U-3, U-4)

```text
feat(admin): features events (distribution/list/heatmap) y visits (list/landing-pages)

- events: chart de distribution + heatmap dia x hora + DataTable virtual de list
- visits: DataTable virtual de list + ranking de landing-pages
- staleTime: agregadas 60s, listados crudos 30s
- Tests unit contra MSW
```

Archivos: `admin/src/features/{events,visits}/**`,
`admin/src/app/(admin)/{events,visits}/**`, tests mirror.

#### Commit 22 — Features `geo` + `devices` + `funnel` (U-5, U-6)

```text
feat(admin): features geo (by-country), devices (breakdown) y funnel (conversion)

- geo/by-country: DataTable ordenada desc por sessions
- devices/breakdown: 3 charts (device_type, browser, os)
- funnel/conversion: chart de embudo session->visit->contact con rates
- Cache backend 60s -> staleTime 60s; tests unit contra MSW
```

Archivos: `admin/src/features/{geo,devices,funnel}/**`,
`admin/src/app/(admin)/{geo,devices,funnel}/**`, tests mirror.

#### Commit 23 — Feature `contacts` (U-7)

```text
feat(admin): feature contacts (list + by-status)

- list: DataTable virtual con filtro status/niche (NO persiste en cache — PII)
- by-status: chart de distribucion por status
- staleTime: list 30s, by-status 60s; tests unit contra MSW
```

Archivos: `admin/src/features/contacts/**`,
`admin/src/app/(admin)/contacts/**`, tests mirror.

---

### Commit 24 — E2E UI + cleanup (ultimo commit)

```text
test(admin): spec E2E de metricas + elimina spec efimera

- tests/feature/admin/metrics.spec.ts: login -> navega /metrics, /sessions, /events, ... -> renderiza
- docs/specs/b-analytics-api/: eliminada (efimera, plan full-stack implementado)
```

Archivos:

- `tests/feature/admin/metrics.spec.ts` (crear)
- `git rm -r docs/specs/b-analytics-api/`

Este commit incluye la **verificacion E2E completa** (seccion 11),
backend Y frontend:

- Bateria de curls contra dev (los 19 endpoints) + smoke de auth (401 sin Bearer)
- Coverage gate verde del Lambda Y del admin
- UI de metricas renderiza en el shell (Lambda vivo o MSW)
- Logs CloudWatch sin ERROR; rate-limit rule confirmada en DDB

Verify (ANTES de commit):

```bash
# Backend — todo verde
python devtools/run.py serverless tests --type=unit --lambda=analytics
python devtools/run.py serverless tests --type=integration --lambda=analytics --aws-profile=tfs-dev
python devtools/run.py serverless tests --type=coverage --lambda=analytics  # >= 80% per-file
python devtools/run.py serverless lint-deps --lambda=analytics
# Frontend — todo verde
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test:coverage   # >= 80% per-file
pnpm --filter @portfolio/admin build           # admin/out/ con /metrics, /sessions, ...
python devtools/run.py test_runner --module=feature --type=feature --env=local
# Smoke contra dev: usar los curls de la bateria B.1..B.6 + el smoke de UI
# en 11-verificacion-e2e.md (los `curl`/pasos inline son la fuente de
# verdad del test E2E manual).
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
| 7 | feature/X | + auth guard | unit `auth_guard` + `jwt_service` |
| 8 (P-1) | feature/X (o worktree) | + analytics op | unit analytics |
| 9 (P-2) | + worktree | + events op | unit events |
| 10 (P-3) | + worktree | + sessions op | unit sessions |
| 11 (P-4) | + worktree | + visits op | unit visits |
| 12 (P-5) | + worktree | + geo + devices | unit geo + devices |
| 13 (P-6) | + worktree | + funnel | unit funnel |
| 14 (P-7) | + worktree | + contacts | unit contacts |
| 15 | feature/X | + integration | integration 6 flujos |
| 16 | feature/X | + SnapStart | deploy dev + Restore < 1500ms |
| 17 | feature/X | + docs backend | `markdownlint` |
| 18 (U-0) | feature/X | + query-keys + MSW | unit `src/mocks` |
| 19 (U-1) | feature/X (o worktree) | + feature analytics | unit admin analytics |
| 20 (U-2) | + worktree | + feature sessions (tracking) | unit admin sessions |
| 21 (U-3,U-4) | + worktree | + features events + visits | unit admin events/visits |
| 22 (U-5,U-6) | + worktree | + features geo + devices + funnel | unit admin geo/devices/funnel |
| 23 (U-7) | + worktree | + feature contacts | unit admin contacts |
| 24 | feature/X | + E2E UI + cleanup | bateria E2E completa (backend + frontend) |

## PR

Un solo PR: `feature/b-analytics-api -> dev` (cubre backend + frontend).

Body del PR (ver `git-workflow.md`, 4 secciones):

```markdown
## Problema
1. El backend persiste sessions/visits/events/contacts en Neon pero no hay forma de leerlos sin abrir `psql`.
2. El panel admin del portfolio necesita una API HTTP autenticada que exponga KPIs, timeseries, rankings y listados, mas la UI que la consuma.

## Solucion
1. Nuevo Lambda `analytics` (GET `/analytics?operation=...&action=...`) con 19 actions en 8 operations, auth con access JWT via `jwt_service.py` + `auth_guard.py` portados al Lambda (no via shared.auth), rate-limit 10 req/min/IP, cache 60s en agregadas, SnapStart.
2. UI de metricas (features Next.js en `admin/`) montada en el app shell del admin (de `a-admin`) bajo `/metrics` + rutas por feature, consumiendo el Lambda con Authorization Bearer.

## Como probar
```bash
# Backend
python devtools/run.py serverless tests --type=coverage --lambda=analytics  # >= 80%
python devtools/run.py serverless deploy --lambda=analytics --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --endpoint=/analytics --limit=10 --window=60 --stage=dev --aws-profile=tfs-dev
# Smoke con auth (401 sin Bearer, 200 con JWT valido)
curl -sS -o /dev/null -w '%{http_code}\n' "https://api.portfolio.dev.the-full-stack.com/analytics?operation=analytics&action=overview"  # 401
curl -H "Authorization: Bearer $JWT" "https://api.portfolio.dev.the-full-stack.com/analytics?operation=analytics&action=overview&from=2026-04-27&to=2026-05-27"  # 200
# Frontend
pnpm --filter @portfolio/admin test:coverage   # >= 80%
pnpm --filter @portfolio/admin build           # admin/out/ con /metrics, /sessions, ...
python devtools/run.py test_runner --module=feature --type=feature --env=local
```

## TODO
- Scope admin / anonimizacion de PII en metricas — fuera de scope (Decision 1: cualquier user autenticado lee, trade-off PII consciente).
- Gestion de CV (plan futuro c-cv-management) — placeholder en el sidebar del admin.
```

> Depende de `a-admin` mergeado (app shell + auth + api-client). Si el
> Lambda `analytics` aun no esta vivo en el env, la UI corre contra MSW.

[< 08-descomposicion-paralelizacion](08-descomposicion-paralelizacion.md) | [Siguiente: 10-paralelizacion-worktrees >](10-paralelizacion-worktrees.md)
