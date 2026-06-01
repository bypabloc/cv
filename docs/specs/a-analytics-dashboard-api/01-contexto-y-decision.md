# 01 — Contexto y decision

[< README](README.md) | [Siguiente: 02-arquitectura >](02-arquitectura.md)

## 1. Contexto / Problema

El backend serverless ya persiste data del visitante en Neon
PostgreSQL — sessions, visits, tracking events y contacts — pero no hay
forma de **leerla** desde afuera. Hoy solo se puede inspeccionar abriendo
`psql` contra la connection string del SSM (operacion manual, sin
agregaciones, sin UI).

Para construir un dashboard de analytics del portfolio (KPIs, series
temporales, rankings, listados crudos) se necesita una API HTTP que
exponga la data agregada y paginada. El dashboard se construira despues
en una iteracion separada; este plan entrega SOLO el backend
(API + queries + cache + rate-limit).

### Constraints

- **Free tier**: Neon free (0.5 GB + 191.9h compute/mes), DynamoDB
  On-Demand free tier perpetuo. El costo de la nueva Lambda + sus
  queries debe quedar dentro del free tier.
- **Patron del repo**: el backend ya tiene 6 Lambdas Python siguiendo el
  patron `lambda-controller` (operation + action -> controller +
  service). El Lambda nuevo SIGUE el mismo patron — no se introduce un
  framework distinto.
- **Sin auth real**: el dashboard es de uso unico-usuario (yo) en esta
  fase. El rate-limit + el hecho de que la URL no este publicada en
  ningun lado son la unica barrera. La proxima iteracion puede sumar
  Cloudflare Access encima sin cambiar el backend.
- **Lectura unicamente**: el Lambda NO escribe a Neon ni a DynamoDB
  (mas alla del cache + rate-limit buckets). No hay endpoints `POST/PUT`.

### Hallazgos de exploracion (resumen)

- `cv` Lambda es el analogo mas cercano: GET + SQL + JSON. Reusar el
  patron.
- `tracking_pixel` Lambda es el analogo para rate-limit + cache.
- `shared.lambda_kit.http_handler` ya maneja GET + query params:
  extrae `operation`/`action` del query string, el resto a `data`.
- `shared.rate_limit.check_or_raise` se llama explicito desde el
  controller (NO esta dentro de `http_handler`).
- `shared.cache.cached` es un decorator (TTL + namespace + tags).
- `shared.db` re-exporta SQLAlchemy + `db_session` context manager.
- `shared.db.url.resolve_database_url` lee `DATABASE_URL` o `DB_URL` o
  el path SSM `SSM_NEON_URL_PATH`.
- `serverless/lambda/resources/dynamodb/rate-limit-rules.yaml` declara
  la TABLA — las **reglas** se cargan en runtime desde esa tabla. No
  hay YAML centralizado de reglas; cada Lambda inserta su propia
  regla al provisionarse, o la insertamos via `serverless run --lambda=db`
  con un seed.
- CI/CD `deploy-backend.yml` auto-detecta Lambdas nuevas por path; con
  agregar la carpeta + manifest, el matrix lo recoge.

## 2. Solucion Propuesta

Crear un Lambda Python `analytics` en
`serverless/lambda/services/analytics/` con la estructura
`lambda-controller` estandar:

```
analytics/
├── manifest.yaml              # GET /analytics, memory 512, SnapStart, neon-url
├── pyproject.toml             # deps = [] (cierre transitivo de shared/)
├── events/                    # eventos de ejemplo para serverless run
│   ├── overview.json
│   ├── timeseries.json
│   ├── ...
└── core/
    ├── handler.py             # http_handler con event_model + cors='public'
    ├── settings/
    │   ├── config.py          # AppConfig + ErrorCode + LogMetricType
    │   └── operations.py      # OPERATIONS (analytics, events, sessions, ...)
    ├── models/                # un Pydantic por dominio
    │   ├── analytics.py
    │   ├── events.py
    │   ├── sessions.py
    │   ├── visits.py
    │   ├── geo.py
    │   ├── devices.py
    │   ├── funnel.py
    │   └── contacts.py
    ├── controllers/
    │   ├── analytics/{overview,timeseries,top_pages,top_referrers,top_niches,active_now,retention}.py
    │   ├── events/{distribution,list,heatmap}.py
    │   ├── sessions/{list,detail}.py
    │   ├── visits/{list,landing_pages}.py
    │   ├── geo/by_country.py
    │   ├── devices/breakdown.py
    │   ├── funnel/conversion.py
    │   └── contacts/{list,by_status}.py
    ├── services/              # logica de negocio + queries SQL
    │   ├── analytics_service.py
    │   ├── events_service.py
    │   ├── sessions_service.py
    │   ├── visits_service.py
    │   ├── geo_service.py
    │   ├── devices_service.py
    │   ├── funnel_service.py
    │   └── contacts_service.py
    └── utils/
        └── rate_limit_guard.py  # helper para llamar check_or_raise con el endpoint fijo
```

Cada action es un controller delgado que:

1. Llama a `check_or_raise(ip, endpoint='/analytics', country)` (rate
   limit + blacklist + country rules).
2. Llama al service correspondiente con `self.validated_data`.
3. Empaqueta la respuesta en el shape estandar `{is_valid, data, code}`.

El service hace la query SQL (via `db_session` + SQLAlchemy 2.x), agrega
si corresponde, y devuelve `dict` serializable. Las queries agregadas
estan decoradas con `@cached(ttl=60, namespace='analytics:<action>',
tags=['analytics-aggregate'])`. Los listados crudos NO se cachean.

### Decisiones clave

- **Decision 1: GET con query params (no POST con body)** — el dashboard
  hace requests idempotentes de lectura; GET es semanticamente correcto
  y cacheable a futuro a nivel CDN. `http_handler` ya soporta GET
  extrayendo operation/action/data del query string.
- **Decision 2: 1 Lambda + multiples operations (no 1 Lambda por dominio)**
  — el grafo de queries es chico y comparte conexion a Neon. Splittear
  multiplica cold starts y costos sin beneficio.
- **Decision 3: Controllers delgados, services gruesos** — la query
  SQL vive en el service. El controller solo orquesta (rate-limit +
  service-call + shape). Esto permite testear queries sin levantar
  todo el evento Lambda.
- **Decision 4: Cache SOLO en agregadas** — overview, timeseries,
  rankings, distribuciones, heatmap. Los listados crudos cambian con
  cada visita nueva (filtros distintos por request); cachearlos
  desperdicia espacio.
- **Decision 5: SnapStart habilitado** — el dashboard se usa
  esporadicamente (no hay invocaciones constantes que mantengan el
  container warm). El cold start sin SnapStart es ~3-5s; con
  SnapStart cae a ~800ms. Patron ya probado en `contact_form`.
- **Decision 6: Default 30d / max 90d** — la tabla
  `vis_tracking_events` esta particionada por mes; queries sobre
  ventanas de 30d tocan 1-2 particiones (rapido). 90d toca hasta 4
  particiones (aceptable). >90d se rechaza con 400.
- **Decision 7: Reusar `shared.rate_limit` (no WAF)** — patron
  consolidado del repo, $0/mes vs $7/mes WAF, suficiente para el
  caso de uso.
- **Decision 8: `cors_origin='public'`** — el dashboard frontend aun
  no existe; al exponer CORS publico, se puede testear desde
  `localhost:3000` o cualquier herramienta sin redeploy. No expone
  riesgo porque la API ya tiene rate-limit.

## 3. Criterios de Aceptacion (AC)

Numerados, BDD-style. Cada test del plan referencia uno o varios.

- **AC-1**: Given una request `GET /analytics?operation=analytics&action=overview&from=2026-04-27&to=2026-05-27`, When la API procesa, Then responde 200 con `{is_valid: true, code: 0, data: {sessions, visits, events, contacts, unique_visitors, avg_visit_duration_sec, bounce_rate}}`.

- **AC-2**: Given una request sin `from`/`to`, When la API procesa, Then aplica defaults (ultimos 30d) y responde 200 con la misma forma de payload.

- **AC-3**: Given una request con `from`/`to` > 90 dias, When la API procesa, Then responde 400 con `code=1001` y mensaje "rango de fechas excede el maximo permitido (90 dias)".

- **AC-4**: Given una request con `operation` o `action` invalido, When la API procesa, Then responde 400 con `code=1000` y un mensaje que liste los valores validos.

- **AC-5**: Given un cliente que excede 10 req/min desde la misma IP, When la 11va request llega dentro del minuto, Then responde 429 con `code=4290` y header `Retry-After`.

- **AC-6**: Given una IP en la blacklist, When llega una request, Then responde 403 con `code=4030` (sin consumir slot del rate-limit).

- **AC-7**: Given una request a `analytics/timeseries` con `bucket=day` y rango 7d, When la API responde, Then `data.points` tiene 7 elementos con `{timestamp, count, niche?, event_type?}` y `data.bucket == "day"`.

- **AC-8**: Given dos requests identicas a `analytics/overview` con cache miss y luego hit dentro de 60s, When la segunda request llega, Then el response es **identico** y el header `x-cache: HIT` (o equivalente en logs) confirma cache hit.

- **AC-9**: Given una request a `events/list` con `page=2&page_size=50`, When la API responde, Then `data.items` tiene hasta 50 items, `data.page == 2`, `data.page_size == 50`, `data.total >= items.length` y `data.has_more` es boolean.

- **AC-10**: Given una request a `events/list` con `page_size=500` (sobre el max), When la API procesa, Then responde 400 con `code=1002` y mensaje "page_size excede el maximo permitido (200)".

- **AC-11**: Given una request a `sessions/detail?session_id=<X>` con sesion inexistente, When la API responde, Then devuelve 404 con `code=4040` y `data=null`.

- **AC-12**: Given una request a `sessions/detail?session_id=<X>` valida, When la API responde, Then `data` incluye `{session, visits: [...], events_count}` con la session, sus visits (todos), y el total de eventos asociados.

- **AC-13**: Given una request a `geo/by-country` rango 30d, When la API responde, Then `data.items` esta ordenado desc por `sessions`, cada item tiene `{country, sessions, visits, events}`, y `data.total` es la suma de sessions.

- **AC-14**: Given una request a `devices/breakdown` rango 30d, When la API responde, Then `data` tiene tres listas: `device_types`, `browsers`, `os`, cada una ordenada desc por sessions.

- **AC-15**: Given una request a `funnel/conversion` rango 30d, When la API responde, Then `data` tiene `{sessions, visits, contacts, session_to_visit_rate, visit_to_contact_rate, session_to_contact_rate}` con los rates como floats 0.0-1.0.

- **AC-16**: Given una request a `contacts/list?status=new&page=1`, When la API responde, Then `data.items` solo contiene contacts con `status='new'`, paginados normalmente.

- **AC-17**: Given una request a `analytics/active-now`, When la API procesa, Then `data` tiene `{active_sessions, threshold_minutes: 5, as_of: <iso8601>}` con el conteo de sessions cuyo `last_seen_at >= now() - 5min`.

- **AC-18**: Given una request a `analytics/retention` rango 30d, When la API responde, Then `data` tiene `{new_visitors, returning_visitors, total, returning_rate}` calculado sobre `vis_sessions` agrupado por `first_seen_at`.

- **AC-19**: Given un cold start del Lambda con SnapStart habilitado, When llega la primera request, Then el Restore Duration (CloudWatch) es < 1500ms y la respuesta total al cliente < 2000ms.

- **AC-20**: Given el Lambda recien deployado a `dev`, When se corre `serverless lint-deps --lambda=analytics`, Then exit code es 0 (cero imports prohibidos en `core/`, cero deps duplicadas con `shared/`).

- **AC-21**: Given los tests unit + integration del Lambda, When se corre `serverless tests --type=coverage --lambda=analytics`, Then el coverage per-file >= 80% en `core/`.

- **AC-22**: Given el smoke E2E contra dev/stage/prod (curl con todos los endpoints), When todas las requests pasan, Then cada endpoint responde con su shape esperado y los logs CloudWatch no muestran ningun ERROR/WARN.

[< README](README.md) | [Siguiente: 02-arquitectura >](02-arquitectura.md)
