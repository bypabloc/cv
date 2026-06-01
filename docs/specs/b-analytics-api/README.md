# Plan: Lambda `analytics` + UI de metricas del admin (full-stack)

> Plan FULL-STACK en dos entregables:
>
> 1. **Backend**: Lambda Python nuevo (`serverless/lambda/services/analytics/`)
>    que expone un API GET `/analytics?operation=<X>&action=<Y>&...` para
>    alimentar las metricas de visitas/tracking. Lee de Neon (tablas `vis_*`
>    + `tax_*`), valida el access JWT en cada request (require_active_user
>    via `shared.auth`), aplica rate-limit 10 req/min/IP via
>    `shared.rate_limit`, cachea queries agregadas con TTL 60s via
>    `shared.cache`. SnapStart habilitado.
> 2. **UI de metricas** (Next.js): las features de metricas que se montan
>    DENTRO del app shell del admin (`admin-shell`, plan `a-admin`):
>    `analytics`, `sessions` (de tracking), `events`, `visits`, `geo`,
>    `devices`, `funnel`, `contacts`. Las rutas son `/metrics` o por feature
>    (`/analytics`, `/sessions`, ...), NUNCA `/dashboard`.
>
> Orden: el plan `a-admin` (app shell) va PRIMERO; este va DESPUES (la UI de
> metricas necesita el shell donde montarse). El Lambda se sigue llamando
> `analytics`.

## Cuando leer

| Tema | Archivo |
|------|---------|
| Problema, solucion, AC numerados | [01-contexto-y-decision.md](01-contexto-y-decision.md) |
| Arquitectura: operations/actions, Pydantic, controllers, services | [02-arquitectura.md](02-arquitectura.md) |
| Infraestructura: manifest, API GW, rate-limit rules, IAM, SnapStart | [03-infraestructura.md](03-infraestructura.md) |
| Queries SQL por endpoint + indices necesarios | [04-queries-sql.md](04-queries-sql.md) |
| Capa de cache: claves, TTL, tags, que NO se cachea | [05-cache-layer.md](05-cache-layer.md) |
| Estrategia de testing (unit por capa + integration smoke) | [06-testing.md](06-testing.md) |
| Listado de archivos afectados con verificacion por archivo | [07-archivos-afectados.md](07-archivos-afectados.md) |
| Descomposicion en tareas atomicas paralelizables | [08-descomposicion-paralelizacion.md](08-descomposicion-paralelizacion.md) |
| Commits incrementales (Conventional Commits espanol) | [09-commits.md](09-commits.md) |
| Paralelizacion con git worktrees | [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) |
| Verificacion E2E iterativa (fase final, gate del PR) | [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Estado por fase

> Las fases del BACKEND (Lambda) van primero; las fases de la UI de
> metricas (Next.js, features que se montan en el app shell del admin)
> se ejecutan despues de que el plan `a-admin` entregue el shell.

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Plan escrito + carpeta `docs/specs/b-analytics-api/` commiteada | pending |
| 1 | Scaffold + manifest + AppConfig + handler vacio | pending |
| 2 | EventModel + OPERATIONS + modelos Pydantic por dominio | pending |
| 3 | Service `analytics` (overview, timeseries, top-pages, top-referrers, top-niches, active-now, retention) | pending |
| 4 | Service `events` (distribution, list, heatmap) | pending |
| 5 | Service `sessions` (list, detail) + `visits` (list, landing-pages) | pending |
| 6 | Service `geo` (by-country) + `devices` (breakdown) | pending |
| 7 | Service `funnel` (conversion) + `contacts` (list, by-status) | pending |
| 8 | Capa de cache (`@cached`) en queries agregadas | pending |
| 9 | Rate-limit rule + integracion `check_or_raise` | pending |
| 10 | Auth (require_active_user via `shared.auth`) + CORS echo/restringido + jwt-secret en manifest/IAM | pending |
| 11 | SnapStart + warmup hook + ajustes manifest | pending |
| 12 | UI de metricas (Next.js): features `analytics`, `sessions`, `events`, `visits`, `geo`, `devices`, `funnel`, `contacts` montadas en el app shell del admin (requiere `a-admin` mergeado) | pending |
| 13 | Verificacion E2E (backend + UI) + limpieza de `docs/specs/b-analytics-api/` | pending |

## Decisiones no-reabribles

Estas decisiones se cerraron en el dialogo previo y NO se vuelven a
discutir en la fase de implementacion:

1. **Auth**: el Lambda valida el access JWT en CADA request
   (`require_active_user` / `verify_jwt` de `shared.auth`, mismo patron que
   `mfa.*`/`webauthn.*` del Lambda `auth`). Lee `_meta.authorization`
   (`Authorization: Bearer <access JWT>`); sin JWT valido/expirado -> 401.
   SIN scope admin: cualquier user autenticado lee metricas (NO whitelist).
   Trade-off PII asumido conscientemente (ver Decision 7). El rate-limit es
   segunda capa. (Invierte la decision previa "solo rate-limit sin auth".)
2. **Rate limit**: 10 req/min/IP estricto (regla self-managed via
   `shared.rate_limit`, NO WAF) — segunda capa, detras del JWT.
3. **HTTP**: GET con query params, parseado por `http_handler` del repo
   (operation y action son query params; el resto del payload tambien).
   El access JWT viaja en el header `Authorization`, no en query params.
4. **Nombre Lambda**: `analytics` (NO `dashboard` ni `admin`).
5. **Ruta API GW**: `GET /analytics`.
6. **Operations**: 7 dominios (`analytics`, `events`, `sessions`, `visits`,
   `geo`, `devices`, `funnel`, `contacts`).
7. **PII**: exponer crudo (IP, country, user_agent). Trade-off CONSCIENTE:
   el registro auth es abierto, asi que cualquier user registrado (sin
   whitelist admin) ve metricas con PII de visitantes. Aceptado
   explicitamente; mitigaciones futuras (scope admin, anonimizar) quedan
   fuera de este plan.
8. **Cache**: DynamoDB TTL 60s SOLO en queries agregadas (overview,
   timeseries, rankings, distribuciones). Listados crudos NO se cachean.
9. **Defaults de paginacion**: `from`/`to` default 30d, max 90d.
   `page_size` default 50, max 200.
10. **SnapStart**: habilitado.
11. **Frontend**: este plan es FULL-STACK. Ademas del backend, entrega la
    UI de metricas (Next.js) que se monta en el app shell del admin
    (`admin-shell`, plan `a-admin`). CORS `echo` (refleja el Origin del
    admin) o restringido a `admin.portfolio.{env}.the-full-stack.com` — NO
    `'*'`. Orden: `a-admin` primero (entrega el shell), este despues.
12. **DB**: Neon PostgreSQL (no DynamoDB) — la data del visitante ya esta
    proyectada ahi por los Lambdas de tracking/contacto que escriben a
    Neon.

## Reglas criticas (siempre activas)

- **SIEMPRE** los services importan paquetes externos via
  `shared.<subpaquete>` (ver
  [.claude/rules/lambda-shared-imports.md](../../.claude/rules/lambda-shared-imports.md)).
- **SIEMPRE** un controller por action; nombre de clase
  `action.capitalize()`.
- **SIEMPRE** la logica de negocio vive en `core/services/`, NUNCA en el
  handler ni en los controllers.
- **SIEMPRE** verificar antes de commitear (lint + tests unit del scope).
- **NUNCA** queries `SELECT *` sin LIMIT explicito; siempre paginar.
- **NUNCA** loguear valores de `DATABASE_URL`, IP de visitantes o
  contenido del email/message de un contact.
- **NUNCA** ejecutar la query del listado de `vis_tracking_events` sin
  filtro `created_at >= X` (la tabla esta particionada por mes).

## Matriz de verificacion (rapida)

| Capa | Comando |
|------|---------|
| Sintaxis Python | `python -m compileall -q serverless/lambda/services/analytics` |
| Imports shared-only | `python devtools/run.py serverless lint-deps --lambda=analytics` |
| Tests unit | `python devtools/run.py serverless tests --type=unit --lambda=analytics` |
| Tests integration | `python devtools/run.py serverless tests --type=integration --lambda=analytics` |
| Coverage | `python devtools/run.py serverless tests --type=coverage --lambda=analytics` |
| Run local (RIE) | `python devtools/run.py serverless run --stage=local --lambda=analytics --event=events/overview.json` |
| Deploy dev | `python devtools/run.py serverless deploy --lambda=analytics --stage=dev --aws-profile=tfs-dev` |
| Smoke E2E | `curl -H "Authorization: Bearer <access JWT>" "https://api.portfolio.dev.the-full-stack.com/analytics?operation=analytics&action=overview&from=2026-04-27&to=2026-05-27"` |

## Bibliografia interna

- [.claude/rules/lambda-controller.md](../../.claude/rules/lambda-controller.md) — formato Lambda Python
- [.claude/rules/lambda-shared-imports.md](../../.claude/rules/lambda-shared-imports.md) — catalogo de portadores
- [.claude/rules/neon-management.md](../../.claude/rules/neon-management.md) — Neon en runtime
- [.claude/rules/serverless-secrets.md](../../.claude/rules/serverless-secrets.md) — SSM + IAM scopes
- [.claude/rules/ci-cd-pipeline.md](../../.claude/rules/ci-cd-pipeline.md) — `deploy-backend.yml` auto-detect
- [.claude/docs/serverless-backend/README.md](../../.claude/docs/serverless-backend/README.md) — arquitectura general
- [.claude/docs/serverless-rate-limit/README.md](../../.claude/docs/serverless-rate-limit/README.md) — sliding window
- [.claude/docs/dynamodb-cache/README.md](../../.claude/docs/dynamodb-cache/README.md) — @cached
- [docs/diagrams/db-er.mmd](../../diagrams/db-er.mmd) — schema Neon
- [serverless/lambda/services/cv/](../../../serverless/lambda/services/cv/) — Lambda analogo (GET + SQL + JSON)
- [serverless/lambda/services/tracking_pixel/](../../../serverless/lambda/services/tracking_pixel/) — Lambda analogo (rate-limit + cache)
