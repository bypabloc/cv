# 08 — Descomposicion para paralelizacion

[< 07-archivos-afectados](07-archivos-afectados.md) | [Siguiente: 09-commits >](09-commits.md)

> Tareas atomicas que pueden ejecutarse por agentes paralelos (humanos o
> Claude subagents) en git worktrees independientes. Cada tarea respeta:
>
> 1. **File Exclusivity** — ningun archivo aparece en dos tareas
>    paralelas.
> 2. **Interface Stability** — los modulos compartidos
>    (`shared/`, `_common.py`, `OPERATIONS`) NO se modifican una vez
>    comprometidos en la base secuencial.
> 3. **Bounded Scope** — cada tarea entrega una unidad cerrada con
>    tests verdes propios.
>
> El plan es FULL-STACK con DOS tracks: **Backend** (Lambda `analytics`,
> tareas `B-*`/`P-*`/`F-*`) y **Frontend** (UI de metricas, tareas
> `U-*`). El track backend NO depende de `a-admin`. El track frontend SI:
> cada `U-*` arranca solo cuando `a-admin` haya entregado el shell
> (`admin-shell`), el `useAuthStore` y el `api-client` con Bearer/refresh.
> Hasta que el Lambda este vivo, las features `U-*` corren contra MSW.

## Base secuencial (NO paralelizable)

Estas tareas son prerequisito de todo el resto. Se ejecutan en el orden
listado, una sola persona/agente, en la rama principal de trabajo.

| # | Tarea | Archivos | Verify | Done |
|---|-------|----------|--------|------|
| B-1 | Crear carpeta del plan + docs | `docs/specs/b-analytics-api/**` (12 archivos .md) | `markdownlint docs/specs/b-analytics-api/*.md` | Plan completo escrito |
| B-2 | Verificar indices Neon + agregar migration si faltan | `serverless/lambda/shared/db/alembic/versions/<rev>_analytics_indexes.py` (condicional) | `psql -c "\\di vis_*"`; si falta indice, migration y `serverless run --lambda=db --event=events/migrate.json --stage=dev` | Indices presentes en dev |
| B-3 | Scaffold del Lambda + manifest + pyproject + .gitignore + README | `serverless/lambda/services/analytics/{manifest.yaml,pyproject.toml,.gitignore,README.md,core/__init__.py}` | `uv sync` en la carpeta; `serverless lint-deps --lambda=analytics` exit 0 | Lambda visible para devtools |
| B-4 | Settings: `config.py` + `operations.py` con TODOS los entries declarados (controllers vacios despues los rellenamos) | `core/settings/{config.py,operations.py,__init__.py}` | `python -c "from core.settings.operations import OPERATIONS; assert len(OPERATIONS) == 8"` | OPERATIONS registrado |
| B-5 | Modelos comunes + handler skeleton + rate_limit_guard | `core/models/_common.py`, `core/handler.py`, `core/utils/rate_limit_guard.py` | `pytest tests/unit/models/test__common*.py tests/unit/utils/ -v` | Handler boots con OPERATIONS vacio (404 unknown op) |
| B-6 | conftest.py raiz + estructura de tests | `tests/conftest.py`, `tests/unit/__init__.py`, `tests/unit/_helpers.py`, `tests/integration/conftest.py`, `tests/integration/_fixtures/**` | `pytest tests/ -v` (todos pasan; ninguno aun) | Test infra lista |
| B-7 | Lambda `db`: command `seed-rate-limit-rule` + event JSON | `serverless/lambda/services/db/core/commands/seed_rate_limit_rule.py`, handler.py mod, `events/seed_rate_limit_analytics.json`, tests del command | `pytest serverless/lambda/services/db/tests/unit/commands/test_seed_rate_limit_rule.py`; `serverless run --stage=local --lambda=db --event=events/seed_rate_limit_analytics.json` | Rule seeder funciona en local |

**Total base secuencial**: 7 tareas. Estimado: 1-2 dias de trabajo.

Tras B-7, las **7 fases siguientes son paralelizables** porque cada
una toca archivos disjuntos: 1 dominio = 1 worktree.

## Fases paralelizables (worktree-safe)

Cada fase corresponde a un dominio. Cada controlador es independiente
del otro, comparten solo `_common.py` (ya commiteado) y `OPERATIONS`
(ya commiteado).

### P-1: Operation `analytics` (7 actions)

**Worktree**: `feature/analytics-op-analytics`

| Archivos | Tests |
|----------|-------|
| `core/models/analytics.py` | `tests/unit/models/test_overview_*.py`, `test_timeseries_*.py`, ... |
| `core/services/analytics_service.py` | `tests/unit/services/test_analytics_*.py` |
| `core/controllers/analytics/overview.py` | `tests/unit/controllers/analytics/test_overview_*.py` |
| `core/controllers/analytics/timeseries.py` | `test_timeseries_*.py` |
| `core/controllers/analytics/top_pages.py` | `test_top_pages_*.py` |
| `core/controllers/analytics/top_referrers.py` | `test_top_referrers_*.py` |
| `core/controllers/analytics/top_niches.py` | `test_top_niches_*.py` |
| `core/controllers/analytics/active_now.py` | `test_active_now_*.py` |
| `core/controllers/analytics/retention.py` | `test_retention_*.py` |
| `events/overview.json`, `events/timeseries.json`, ... (7) | — |

**AC referenciados**: AC-1, AC-2, AC-3, AC-4, AC-7, AC-8, AC-17, AC-18.

**Depende de**: B-1 a B-7. **Paralelizable con**: P-2..P-7.

**Verify**:
```bash
python -m compileall -q serverless/lambda/services/analytics/core
python devtools/run.py serverless tests --type=unit --lambda=analytics -- -k "analytics or overview or timeseries or top_pages or top_referrers or top_niches or active_now or retention"
python devtools/run.py serverless run --stage=local --lambda=analytics --event=events/overview.json
```

**Done**: 7 actions corren contra DB local, devuelven shape correcta.

---

### P-2: Operation `events` (3 actions)

**Worktree**: `feature/analytics-op-events`

| Archivos | Tests |
|----------|-------|
| `core/models/events.py` | `tests/unit/models/test_distribution_*.py`, `test_events_list_*.py`, `test_heatmap_*.py` |
| `core/services/events_service.py` | `tests/unit/services/test_events_*.py` |
| `core/controllers/events/distribution.py` | `tests/unit/controllers/events/test_distribution_*.py` |
| `core/controllers/events/list.py` | `test_list_*.py` |
| `core/controllers/events/heatmap.py` | `test_heatmap_*.py` |
| `events/events_distribution.json`, `events/events_list.json`, `events/events_heatmap.json` | — |

**AC**: AC-4, AC-9, AC-10.

**Depende de**: B-1 a B-7. **Paralelizable con**: P-1, P-3..P-7.

---

### P-3: Operation `sessions` (2 actions)

**Worktree**: `feature/analytics-op-sessions`

| Archivos | Tests |
|----------|-------|
| `core/models/sessions.py` | `tests/unit/models/test_sessions_list_*.py`, `test_sessions_detail_*.py` |
| `core/services/sessions_service.py` | `tests/unit/services/test_sessions_*.py` |
| `core/controllers/sessions/list.py`, `core/controllers/sessions/detail.py` | `tests/unit/controllers/sessions/...` |
| `events/sessions_list.json`, `events/sessions_detail.json` | — |

**AC**: AC-11, AC-12.

---

### P-4: Operation `visits` (2 actions)

**Worktree**: `feature/analytics-op-visits`

| Archivos | Tests |
|----------|-------|
| `core/models/visits.py` | `tests/unit/models/test_visits_*.py` |
| `core/services/visits_service.py` | `tests/unit/services/test_visits_*.py` |
| `core/controllers/visits/list.py`, `core/controllers/visits/landing_pages.py` | `tests/unit/controllers/visits/...` |
| `events/visits_list.json`, `events/visits_landing_pages.json` | — |

**AC**: AC-9.

---

### P-5: Operations `geo` + `devices` (2 actions, 1 worktree)

**Worktree**: `feature/analytics-op-geo-devices`

Razon de combinar: son operations chicas (1 action c/u). Manejarlas en
un solo worktree reduce overhead de gestion.

| Archivos | Tests |
|----------|-------|
| `core/models/geo.py`, `core/models/devices.py` | `tests/unit/models/test_geo_*.py`, `test_devices_*.py` |
| `core/services/geo_service.py`, `core/services/devices_service.py` | `tests/unit/services/test_geo_*.py`, `test_devices_*.py` |
| `core/controllers/geo/by_country.py` | `tests/unit/controllers/geo/...` |
| `core/controllers/devices/breakdown.py` | `tests/unit/controllers/devices/...` |
| `events/geo_by_country.json`, `events/devices_breakdown.json` | — |

**AC**: AC-13, AC-14.

---

### P-6: Operation `funnel` (1 action)

**Worktree**: `feature/analytics-op-funnel`

| Archivos | Tests |
|----------|-------|
| `core/models/funnel.py` | `tests/unit/models/test_funnel_*.py` |
| `core/services/funnel_service.py` | `tests/unit/services/test_funnel_*.py` |
| `core/controllers/funnel/conversion.py` | `tests/unit/controllers/funnel/test_conversion_*.py` |
| `events/funnel_conversion.json` | — |

**AC**: AC-15.

---

### P-7: Operation `contacts` (2 actions)

**Worktree**: `feature/analytics-op-contacts`

| Archivos | Tests |
|----------|-------|
| `core/models/contacts.py` | `tests/unit/models/test_contacts_*.py` |
| `core/services/contacts_service.py` | `tests/unit/services/test_contacts_*.py` |
| `core/controllers/contacts/list.py`, `core/controllers/contacts/by_status.py` | `tests/unit/controllers/contacts/...` |
| `events/contacts_list.json`, `events/contacts_by_status.json` | — |

**AC**: AC-16.

## Fases finales (post-merge de paralelas)

Despues de mergear P-1..P-7 al branch principal:

| # | Tarea | Archivos | Verify | Done |
|---|-------|----------|--------|------|
| F-1 | Tests integration (6 flujos) | `tests/integration/test_*_e2e.py` (6) | `serverless tests --type=integration --lambda=analytics` | 6 integration tests verdes |
| F-2 | Runtime hooks SnapStart | `core/runtime_hooks.py` | `serverless deploy --lambda=analytics --stage=dev`; CloudWatch verifica Restore Duration | Restore Duration < 1500ms |
| F-3 | Seed rate-limit rule (manual via CLI) | (sin codigo: comando) | `serverless run --stage=dev --lambda=db --event=events/seed_rate_limit_analytics.json --aws-profile=tfs-dev` (idem stage/prod) | Rule en DDB en los 3 envs |
| F-4 | Coverage gate | (revision) | `serverless tests --type=coverage --lambda=analytics` >= 80% per-file | AC-21 |
| F-5 | Smoke E2E + docs permanente | `.claude/docs/serverless-backend/03-lambdas.md` mod | `curl https://api.portfolio.dev.../analytics?...` para cada action; bateria pasa | AC-22 |
| F-6 | Eliminar carpeta del plan + ultimo commit | `git rm -r docs/specs/b-analytics-api/` | `test ! -d docs/specs/b-analytics-api` | Spec archivada |

## Track frontend — UI de metricas (`U-*`)

Estas tareas AGREGAN las features de metricas a la app `admin/` (package
`@portfolio/admin`). Dependen de que `a-admin` haya entregado el shell +
`api-client` + `useAuthStore` (prerequisito DURO). Corren en paralelo al
track backend (`B-*`/`P-*`/`F-*`): no comparten archivos. Hasta que el
Lambda `analytics` este vivo, los hooks resuelven contra MSW.

### Base secuencial del frontend

| # | Tarea | Archivos | Verify | Done |
|---|-------|----------|--------|------|
| U-0 | Query-keys raiz + handlers MSW de los 19 endpoints + types base | `admin/src/lib/metrics-query-keys.ts`, `admin/src/mocks/handlers/metrics.ts` | `pnpm --filter @portfolio/admin test -- src/mocks` | MSW responde los 19 endpoints |

### Fases paralelizables del frontend (worktree-safe)

Cada feature = 1 worktree. Comparten solo `metrics-query-keys.ts` +
`api-client` (ya commiteados en U-0 / `a-admin`). 1 feature = archivos
disjuntos bajo `admin/src/features/<feature>/` + su page + sus tests.

| # | Feature | Worktree | Archivos | AC | Verify |
|---|---------|----------|----------|----|--------|
| U-1 | `analytics` | `feature/admin-metrics-analytics` | `admin/src/features/analytics/**`, `admin/src/app/(admin)/metrics/**`, tests | AC-1, AC-7, AC-17, AC-18, AC-25 | `pnpm --filter @portfolio/admin test -- src/features/analytics` |
| U-2 | `sessions` (tracking) | `feature/admin-metrics-sessions` | `admin/src/features/sessions/**`, `admin/src/app/(admin)/sessions/**`, tests | AC-11, AC-12, AC-25 | idem `src/features/sessions` |
| U-3 | `events` | `feature/admin-metrics-events` | `admin/src/features/events/**`, `admin/src/app/(admin)/events/**`, tests | AC-9, AC-25 | idem `src/features/events` |
| U-4 | `visits` | `feature/admin-metrics-visits` | `admin/src/features/visits/**`, `admin/src/app/(admin)/visits/**`, tests | AC-9, AC-25 | idem `src/features/visits` |
| U-5 | `geo` + `devices` | `feature/admin-metrics-geo-devices` | `admin/src/features/{geo,devices}/**`, `admin/src/app/(admin)/{geo,devices}/**`, tests | AC-13, AC-14, AC-25 | idem ambos features |
| U-6 | `funnel` | `feature/admin-metrics-funnel` | `admin/src/features/funnel/**`, `admin/src/app/(admin)/funnel/**`, tests | AC-15, AC-25 | idem `src/features/funnel` |
| U-7 | `contacts` | `feature/admin-metrics-contacts` | `admin/src/features/contacts/**`, `admin/src/app/(admin)/contacts/**`, tests | AC-16, AC-25 | idem `src/features/contacts` |

**Depende de**: `a-admin` mergeado + U-0. **Paralelizable con**: U-1..U-7
entre si, y con el track backend completo.

### Fases finales del frontend

| # | Tarea | Archivos | Verify | Done |
|---|-------|----------|--------|------|
| U-F1 | Spec E2E Playwright del area de metricas | `tests/feature/admin/metrics.spec.ts` | `python devtools/run.py test_runner --module=feature --type=feature --env=local` | login -> navega /metrics, /sessions, ... -> renderiza |
| U-F2 | Coverage gate del admin | (revision) | `pnpm --filter @portfolio/admin test:coverage` >= 80% per-file | AC-25 |
| U-F3 | Build estatico del admin | (revision) | `pnpm --filter @portfolio/admin build` -> `admin/out/` con las rutas /metrics, /sessions, ... | rutas en `out/` |

## Diagrama de dependencias

```text
Track BACKEND (no depende de a-admin):

B-1 ──> B-2 ──> B-3 ──> B-4 ──> B-5 ──> B-6 ──> B-7
                                                  │
                            ┌─────────────────────┼─────────────────────┐
                            │       │       │       │       │       │       │
                           P-1     P-2     P-3     P-4     P-5     P-6     P-7
                            │       │       │       │       │       │       │
                            └───────┴───────┴───────┴───────┴───────┴───────┘
                                                  │
                                          merge a feature/X
                                                  │
                                                F-1 ──> F-2 ──> F-3 ──> F-4 ──> F-5 ──> F-6

Track FRONTEND (depende de a-admin mergeado: shell + api-client):

a-admin merged ──> U-0
                    │
        ┌───────────┼───────────┬───────┬───────┬───────┐
        │     │     │     │     │     │     │
       U-1   U-2   U-3   U-4   U-5   U-6   U-7
        │     │     │     │     │     │     │
        └─────┴─────┴─────┴─────┴─────┴─────┘
                    │
              U-F1 ──> U-F2 ──> U-F3

Ambos tracks convergen en el mismo PR -> dev (cuando los dos esten verdes).
```

## Validacion del paralelismo (File Exclusivity)

Matriz de archivos por fase. Una columna = una fase. Una "X" significa
"esta fase toca este archivo". Ninguna fila tiene mas de una "X" entre
P-1..P-7:

| Archivo / Fase | B | P-1 | P-2 | P-3 | P-4 | P-5 | P-6 | P-7 | F |
|----------------|---|-----|-----|-----|-----|-----|-----|-----|---|
| `core/handler.py` | X | | | | | | | | |
| `core/settings/operations.py` | X | | | | | | | | |
| `core/settings/config.py` | X | | | | | | | | |
| `core/models/_common.py` | X | | | | | | | | |
| `core/utils/rate_limit_guard.py` | X | | | | | | | | |
| `core/models/analytics.py` | | X | | | | | | | |
| `core/models/events.py` | | | X | | | | | | |
| `core/models/sessions.py` | | | | X | | | | | |
| `core/models/visits.py` | | | | | X | | | | |
| `core/models/geo.py` | | | | | | X | | | |
| `core/models/devices.py` | | | | | | X | | | |
| `core/models/funnel.py` | | | | | | | X | | |
| `core/models/contacts.py` | | | | | | | | X | |
| `core/services/analytics_service.py` | | X | | | | | | | |
| `core/services/events_service.py` | | | X | | | | | | |
| `core/services/sessions_service.py` | | | | X | | | | | |
| `core/services/visits_service.py` | | | | | X | | | | |
| `core/services/geo_service.py` | | | | | | X | | | |
| `core/services/devices_service.py` | | | | | | X | | | |
| `core/services/funnel_service.py` | | | | | | | X | | |
| `core/services/contacts_service.py` | | | | | | | | X | |
| `core/controllers/analytics/**` | | X | | | | | | | |
| `core/controllers/events/**` | | | X | | | | | | |
| `core/controllers/sessions/**` | | | | X | | | | | |
| `core/controllers/visits/**` | | | | | X | | | | |
| `core/controllers/geo/**` | | | | | | X | | | |
| `core/controllers/devices/**` | | | | | | X | | | |
| `core/controllers/funnel/**` | | | | | | | X | | |
| `core/controllers/contacts/**` | | | | | | | | X | |
| `events/*.json` | X (event template) | X (7) | X (3) | X (2) | X (2) | X (2) | X (1) | X (2) | |
| `tests/integration/` | X (conftest) | | | | | | | | X |
| `core/runtime_hooks.py` | | | | | | | | | X |

**Validacion**: ninguna fila tiene 2+ "X" entre P-1..P-7. Las celdas con
"X" en `B` son intocables tras B-7. **OK** para paralelizar.

El track frontend (`U-*`) toca SOLO `admin/**` + `tests/feature/admin/**`;
el track backend toca SOLO `serverless/lambda/**`. Cero solape entre
tracks: file exclusivity garantizada por construccion. Dentro del track
frontend, U-1..U-7 tocan `admin/src/features/<feature>/**` +
`admin/src/app/(admin)/<ruta>/**` disjuntos (comparten solo
`metrics-query-keys.ts`, ya commiteado en U-0).

## Granularidad

Backend:

- 7 tareas base secuenciales (B-*).
- 7 fases paralelizables (P-1..P-7), cada una entrega 1 operation.
- 6 tareas finales (F-*).

Frontend:

- 1 tarea base (U-0: query-keys raiz + MSW).
- 7 fases paralelizables (U-1..U-7), cada una entrega 1 feature.
- 3 tareas finales (U-F1..U-F3).

- **Total**: 31 unidades de trabajo. Tamano: Large.

CAP de concurrencia (ver [orchestration.md](../../.claude/rules/orchestration.md)):
**<=4 agentes simultaneos** y **1 workflow a la vez** para no pegar el
rate-limit. Las 14 fases paralelizables (P-1..P-7 + U-1..U-7) se corren
en **olas de <=4**, NO 14 a la vez. El track frontend ademas no puede
arrancar hasta `a-admin` mergeado: en la practica primero corren las olas
de `P-*` (backend) y luego las de `U-*` (frontend).

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Editar `core/settings/operations.py` desde una fase P-X | Es base; rompe el commit anchor | Si una action nueva sale en una fase, mergear secuencialmente al main del feature |
| Tocar `core/models/_common.py` desde P-X | Es base | Idem |
| Crear un controller que pisa otra fase (ej. P-1 toca `events/`) | Rompe file exclusivity | Mover al worktree correcto |
| Lanzar P-X antes de commitear B-7 | Conflictos garantizados | Esperar a tener B-7 mergeado al feature branch local |
| Olvidar registrar la action en `OPERATIONS` | El handler tira 404 | Revisar el archivo `operations.py` ya tiene la entrada (lo dejamos completo en B-4) |
| Arrancar una fase `U-*` antes de que `a-admin` mergee el shell/api-client | No existe donde montar la feature ni como autenticar | Esperar a `a-admin` mergeado + U-0 |
| Nombrar la ruta `/dashboard` o el feature `dashboard` | El producto es `admin`; las metricas van a `/metrics` + por feature | Usar `/metrics`, `/sessions`, ... y el feature `admin-shell` para el shell |
| Confundir la feature `sessions` (tracking) con `sessions-mgmt` (auth) | Son dominios distintos (visitantes vs mi cuenta) | `sessions` (este plan) = tracking; `sessions-mgmt` (a-admin) = auth |
| Llamar `fetch()` directo desde un hook/componente de metricas | Se salta el Bearer + refresh + retry del api-client | Pasar SIEMPRE por `admin/src/lib/api-client.ts` |

[< 07-archivos-afectados](07-archivos-afectados.md) | [Siguiente: 09-commits >](09-commits.md)
