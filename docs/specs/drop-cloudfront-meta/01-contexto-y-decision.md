# 01 — Contexto, Solucion, Criterios de Aceptacion

[← README](README.md) | [02-implementacion.md →](02-implementacion.md)

## 1. Contexto / Problema

6 columnas de Neon **sin consumer real**:

- `tracking_events`: `cloudfront_meta`, `expires_at`, `page_url`,
  `page_title`, `referrer`
- `contacts`: `cloudfront_meta`

Mas el indice parcial `idx_tracking_referrer` que queda huerfano al
dropear `referrer`.

### Estado actual

- **`cloudfront_meta`**: agregada en la migracion
  `b2c3d4e5f6a7_drop_stream_event_id` (commits 2-4 del plan
  `tracking-data-completeness`, mergeado en PR #113). Persiste un dict
  con ~22 headers `cloudfront-*` (`viewer-country/region/city/postal/
  lat/long/metro/time-zone/asn/ja3-fingerprint/tls` + device flags) que
  llegan al Lambda cuando el custom domain del API Gateway es
  Edge-Optimized. Vive en `tracking_events` y `contacts`.

- **`expires_at`** (en `tracking_events` de Neon): era el TTL Unix-epoch
  cuando el flujo era `Lambda -> DynamoDB Stream -> stream_processor ->
  Neon`. Desde la spec `direct-neon-writes` (mayo 2026) el
  `tracking_pixel` escribe directo a Neon y el service lo asigna
  explicitamente a `None` (ver `tracking_service.py:137`). Neon es
  analytics, no cache.

- **`page_url`** (Text NOT NULL): URL completa enviada por el frontend
  desde `location.href`. Sin queries que la consuman.
- **`page_title`** (Text NULL): `document.title` capturado en el momento
  del evento. Sin queries que la consuman.
- **`referrer`** (Text NULL): `document.referrer` capturado en el evento.
  Tiene indice parcial `idx_tracking_referrer` (referrer IS NOT NULL).
  Sin queries que lo consuman.

> Nota: `page_path` (Text NULL) **NO se elimina**. Sigue vivo con su
> indice `idx_tracking_page_path` y es la columna usada para analitica
> de "trafico por seccion" (queries por path canonico, sin URL/query
> strings). `page_url` + `page_title` + `referrer` quedan huerfanas en
> presencia de `page_path`.

### Por que eliminarlas

- **Sin consumer**: ningun query del backend ni del frontend lee
  `cloudfront_meta`. La feature "analitica futura" se documento como
  intencion pero nunca se materializo.
- **`expires_at` huerfano**: cada `INSERT` mete un NULL explicito que
  Postgres almacena igualmente. La columna existe solo por inercia del
  schema viejo de DDB.
- **Costo de schema**: columnas sin uso aumentan la superficie de
  cambio (migraciones futuras, modelos, models en tests, mock fixtures),
  aceleran la entropia.
- **Decision del owner**: explicit user direction de eliminar
  `cloudfront_meta`, con scope extendido a `expires_at`.

### Hallazgos de exploracion

- 13 archivos del backend mencionan `cloudfront_meta`.
- La migracion `b2c3d4e5f6a7` es la unica que toca `cloudfront_meta`;
  no hay indices sobre ella.
- `expires_at` en `tracking_events` (Neon) NO tiene indices ni
  dependencias en queries.
- `expires_at` en DynamoDB cache + `TrackingEventItem` fixture +
  `RateLimitBucketItem` SI usan TTL real de DynamoDB — **no se tocan**.
- `page_url` / `page_title` / `referrer` NO tienen consumer (queries
  ni FK).
- `referrer` tiene indice parcial `idx_tracking_referrer`
  (referrer IS NOT NULL); debe dropearse antes que la columna.
- En `tracking_events` la tabla es PARTITIONED BY RANGE(created_at);
  en PG14+ `drop_column` y `drop_index` propagan automatico a
  particiones.

## 2. Solucion Propuesta

Drop atomico en una nueva migracion Alembic con `down_revision =
'b2c3d4e5f6a7'`. Orden duro en `upgrade()`:

1. `drop_index('idx_tracking_referrer', table_name='tracking_events',
   postgresql_where='referrer IS NOT NULL')`
2. `drop_column('tracking_events', 'referrer')`
3. `drop_column('tracking_events', 'page_title')`
4. `drop_column('tracking_events', 'page_url')`
5. `drop_column('tracking_events', 'expires_at')`
6. `drop_column('tracking_events', 'cloudfront_meta')`
7. `drop_column('contacts', 'cloudfront_meta')`

`downgrade()` invierte el orden (columna primero, indice al final, y
`page_url` se recrea como NULL — no NOT NULL — para que el revert no
falle con la data existente).

En el codigo:

- Drop de las columnas en los modelos SQLAlchemy
  (`tracking_events.{cloudfront_meta, expires_at, page_url, page_title,
  referrer}` y `contacts.cloudfront_meta`), mas la entrada
  `idx_tracking_referrer` de `__table_args__`.
- Drop de las keys en el `neon_payload` de `tracking_service.py`
  (`cloudfront_meta`, `expires_at`, `page_url`, `page_title`,
  `referrer`).
- Drop del kwarg `cloudfront_meta=` que el controller del
  `tracking_pixel` pasa al service.
- Drop del branch en `ContactCreateModel.form_fields()` que inyecta
  `cloudfront_meta` al output.
- Drop de la key `cloudfront_meta` en el `neon_payload` de
  `contact_service.py`.
- **NO** se tocan: el helper
  `shared.http.ip_extractor.extract_cloudfront_meta`, la inyeccion en
  `shared.lambda_kit.http_dispatch`, los campos Pydantic
  (`RequestMeta.cloudfront_meta`, `TrackEventMeta.cloudfront_meta`,
  `TrackEventModel.page_url/page_title/referrer`), ni el frontend
  (`build-track-payload`, `TrackingPixel.astro`).

### Decisiones clave

- **Decision 1: drop forward, downgrade reversible** — la migracion
  permite revertir si aparece algun bug post-deploy. Probada en branch
  Neon antes de aplicar a dev.
- **Decision 2: scope cerrado a Neon** — `expires_at` en DDB (cache,
  rate_limit_bucket, TrackingEventItem fixture) NO se toca. Es TTL real
  con consumer activo.
- **Decision 3: helper + Pydantic fields permanecen** — codigo muerto
  controlado. Si la analitica resurge, el cableado de entrada esta
  listo; solo habria que volver a persistir y recrear las columnas.
  Aplica a:
  - `extract_cloudfront_meta` + inyeccion en `_meta`
  - `RequestMeta.cloudfront_meta` y `TrackEventMeta.cloudfront_meta`
  - `TrackEventModel.page_url`, `TrackEventModel.page_title`,
    `TrackEventModel.referrer`
- **Decision 4: page_path se mantiene** — sigue siendo la columna
  canonica para analitica de "trafico por seccion" (path sin URL/query
  string).
- **Decision 5: page_url en downgrade vuelve como NULL, no NOT NULL** —
  si despues del upgrade hay rows nuevas en `tracking_events`, un
  `downgrade()` no puede recrear page_url como NOT NULL sin un DEFAULT
  o sin romper. Vuelve nullable; quien necesite revertir y exigir NOT
  NULL lo hace en una migracion posterior.
- **Decision 6: un solo PR `feature/drop-cloudfront-meta -> dev`** —
  promocion a stage/main sigue el flujo en cadena del proyecto.
- **Decision 7: migracion en CI a dev/stage/prod via la Lambda `db`** —
  patron estandar: tras mergear, `serverless run --lambda=db
  --event=events/migrate.json` por env, en orden dev -> stage -> prod.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: When alembic ejecuta `upgrade head` sobre un branch Neon
  Then `tracking_events` ya no contiene `cloudfront_meta`, `expires_at`,
  `page_url`, `page_title`, ni `referrer`.
- **AC-2**: When alembic ejecuta `upgrade head` Then `contacts` ya no
  contiene `cloudfront_meta`.
- **AC-3**: When alembic ejecuta `upgrade head` Then el indice
  `idx_tracking_referrer` ya no existe.
- **AC-4**: When alembic ejecuta `downgrade -1` Then las 6 columnas
  vuelven a aparecer (todas NULLABLE) y el indice `idx_tracking_referrer`
  vuelve a crearse.
- **AC-5**: When `tracking_pixel` persiste un evento Then el dict
  `neon_payload` que se pasa a `insert_tracking` no contiene las keys
  `cloudfront_meta`, `expires_at`, `page_url`, `page_title`, ni
  `referrer`.
- **AC-6**: When `contact_form` persiste un contacto Then el dict
  `neon_payload` que se pasa a `insert_contact` no contiene la key
  `cloudfront_meta`.
- **AC-7**: When el handler `/track` recibe un body con headers
  `cloudfront-*` y con `page_url` / `page_title` / `referrer` en el
  payload Then la response sigue siendo `HTTP 204 No Content` y
  no se levantan errores Pydantic.
- **AC-8**: When el handler `/contact` recibe un body con headers
  `cloudfront-*` Then la response sigue siendo `HTTP 201 Created` y
  no se levantan errores Pydantic.
- **AC-9**: When se ejecuta `pnpm exec biome check .` Then 0 errores en
  archivos modificados.
- **AC-10**: When se ejecuta `serverless tests --type=coverage
  --lambda=tracking_pixel` y `--lambda=contact_form` Then coverage
  per-file >= 80% en archivos modificados.
- **AC-11**: When se ejecuta `serverless tests --type=integration
  --lambda=tracking_pixel` y `--lambda=contact_form` Then todos los
  tests E2E pasan con la nueva firma del payload.
- **AC-12**: When se inspecciona el codigo del repo Then
  `shared.http.ip_extractor.extract_cloudfront_meta`,
  `TrackEventModel.page_url/page_title/referrer` y los tests de
  `extract_cloudfront_meta` / `http_handler_injects_meta_from_headers`
  siguen presentes y verdes (decision 3).
- **AC-13**: When se inspecciona `tracking_events` Then `page_path` y
  su indice `idx_tracking_page_path` siguen existiendo intactos.

---

[← README](README.md) | [02-implementacion.md →](02-implementacion.md)
