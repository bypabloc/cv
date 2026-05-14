# SPEC-014: Dashboard Astro protegido que consulta Neon

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: Nueva app `apps/dashboard/` o pagina en `apps/generic/`
**Dependencias**: SPEC-010 (aggregator + daily_metrics + materialized views)
**Paralelizable con**: SPEC-015

## 1. Contexto

Dashboard privado para owner que muestra analytics del portfolio
(contacts CRM-style + page views trends + conversion rate + session
journeys). Datos vienen de Neon PG via Lambda API dedicada.

### Hallazgos de exploracion

- 10 queries listas en `.claude/docs/postgresql-18-analytics/08-queries-dashboard.md`
- Astro 6 SSR posible con adapter (Cloudflare Pages no soporta SSR
  nativo en static hosting). Alternativa: Lambda + API privada.
- Basic auth simple HTTP suficiente para portfolio personal

## 2. Solucion propuesta

Crear endpoint Lambda nuevo + dashboard estatico que consulta via API:

### Backend: nueva Lambda `dashboard_api`

```text
serverless/src/dashboard_api/
├── __init__.py
├── handler.py             # API GW Lambda con basic auth
├── service.py             # orquesta queries con cache @cached(30min)
├── queries.py             # las 10 queries documentadas
├── auth.py                # basic auth contra SSM password hash
├── schemas.py
└── requirements.txt
```

Plus 1 endpoint nuevo `GET /dashboard/metrics?since=7d` en API GW.

### Frontend: pagina `/dashboard` en `apps/generic`

```text
apps/generic/src/pages/dashboard/
├── index.astro            # landing con basic auth prompt + cards
├── contacts.astro         # tabla contactos paginada
├── analytics.astro        # graficos con Chart.js (CDN)
└── _dashboard.client.ts   # fetch API + render charts
```

### Decisiones clave

- **Decision 1: Basic Auth via SSM** — `/portfolio/dashboard-password-hash`
  (bcrypt). Lambda valida en cada request. Mas seguro que basic auth
  hardcoded en Cloudflare Workers.
- **Decision 2: Cache de queries con SWR (30min)** — agregar tag
  `analytics`. El aggregator (SPEC-010) invalida tag al terminar.
- **Decision 3: Chart.js via CDN** — vs bundle. Razon: 80KB cached
  cross-site. Dashboard es low-traffic, ok aceptar TTFB extra.
- **Decision 4: Sin password recovery** — portfolio personal, owner
  rota password via `serverless rotate-secret --name=/portfolio/dashboard-password`.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given visitante anonimo en https://the-full-stack.com/dashboard,
  When carga la pagina, Then browser muestra basic auth prompt
- **AC-2**: Given owner con password correcto, When ingresa
  credenciales, Then ve dashboard con cards (Total contacts mes,
  Total page views mes, Conversion rate, Top landing page)
- **AC-3**: Given owner en /dashboard/contacts, When carga, Then ve
  tabla paginada de contacts (20 per page) ordenada por created_at
  DESC + filtros por niche, service_type, country
- **AC-4**: Given owner en /dashboard/analytics, When carga, Then ve
  3 graficos: page views por dia (linea), top 10 UTM sources (bar),
  device breakdown (pie)
- **AC-5**: Given owner click un contact, When abre detalle, Then ve
  full message + email link + IP + country + UA + form completo + session
  journey del visitante (LAG/LEAD sobre tracking_events)
- **AC-6**: Given password incorrecto 5 veces en 5min, When intenta
  ingresar, Then ve 429 (rate-limit del Lambda dashboard_api)
- **AC-7**: Given queries cacheadas, When primera carga, Then latencia
  warm < 500ms; segunda carga (cache hit) < 100ms
- **AC-8**: Given cache invalidada por aggregator, When recargo
  dashboard, Then datos frescos (refrescados ese mismo cron)

## 4. Diagrama de Flujo

```text
Browser GET /dashboard/contacts?page=2
    |
    v
Basic Auth check (browser nativa)
    |
    v
Astro renderiza HTML con script defer
    |
    v
script fetch GET /dashboard/contacts?since=30d&page=2 (con Basic Auth header)
    |
    v
API GW -> Lambda dashboard_api
    |
    +-- rate-limit (/dashboard, 5/min/IP per password)
    +-- basic_auth verify (SSM bcrypt hash)
    |
    v
@cached(ttl=1800, tags=['analytics']) get_contacts(page, filters)
    |
    +-- cache HIT -> return
    +-- cache MISS -> psycopg3 SELECT FROM contacts ... LIMIT 20 OFFSET ?
    |
    v
return 200 + JSON
    |
    v
Browser renderiza tabla
```

## 5. Diagrama ER

N/A — solo lectura. Usa tablas creadas en SPEC-008 + materialized views
refrescadas por SPEC-010.

## 6. Tests Requeridos

### 6.B. Unit Tests

- `tests/unit/dashboard_api/test_handler.py` — auth + rate-limit
- `tests/unit/dashboard_api/test_queries.py` — testcontainers PG18
- `tests/unit/dashboard_api/test_auth.py` — bcrypt compare

Coverage minimo: 80%.

### 6.D. E2E (Playwright)

- `tests/feature/dashboard/dashboard-access.feature`:
  - Anonimo -> 401
  - Password correcto -> 200 + dashboard renderiza
  - 5 intentos fallidos -> 429

## 7. Archivos Afectados

### Crear (backend)

- `serverless/src/dashboard_api/*.py` (7 archivos)
- `serverless/events/dashboard_metrics.json`
- SSM Parameter `/portfolio/dashboard-password-hash` (manual,
  bcrypt hash de password)

### Crear (frontend)

- `apps/generic/src/pages/dashboard/index.astro`
- `apps/generic/src/pages/dashboard/contacts.astro`
- `apps/generic/src/pages/dashboard/analytics.astro`
- `apps/generic/src/pages/dashboard/_dashboard.client.ts`
- `tests/feature/dashboard/dashboard-access.feature`

### Modificar

- `serverless/template.yaml` — agregar `DashboardApiFunction` + ruta
  `GET /dashboard/*` en API
- `apps/generic/src/middleware.ts` — basic auth header forwarding
- `apps/generic/astro.config.ts` — verificar SSG sigue funcionando
  (dashboard es paginas SSG + JS client fetch)

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | dashboard_api Lambda backend | SPEC-010 | T2 |
| T2 | dashboard frontend pages | T1 (API contract) | T1 |
| T3 | tests Playwright | T1, T2 | — |
| T4 | deploy + bcrypt password setup | T1, T2 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-010 done (datos en daily_metrics + MVs)
- [ ] Password generado + bcrypt hash en SSM

### Definition of Done

- [ ] AC-1 a AC-8 cumplidos
- [ ] Coverage backend >= 80%
- [ ] Tests Playwright pasan
- [ ] Dashboard accesible en https://the-full-stack.com/dashboard
- [ ] Latencia warm < 500ms, cache hit < 100ms
- [ ] Charts renderizan correctamente en mobile + desktop
