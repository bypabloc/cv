# 02 — Diagramas, Tests Requeridos, Archivos Afectados

[← 01-contexto-y-decision.md](01-contexto-y-decision.md) | [03-commits.md →](03-commits.md)

## 4. Diagrama de Flujo

`N/A — el cambio no altera flujos de control. El handler sigue
construyendo el _meta con cloudfront_meta y los Pydantic models siguen
aceptandolo; solo se elimina la persistencia downstream.`

## 5. Diagrama ER (antes / despues)

### Antes

```text
tracking_events (PARTITION BY RANGE(created_at))
├── session_id        TEXT       NOT NULL
├── page_id           UUID       NOT NULL
├── created_at        TIMESTAMPTZ NOT NULL
├── received_at       TIMESTAMPTZ NOT NULL
├── expires_at        TIMESTAMPTZ NULL    ← se elimina
├── page_url          TEXT       NOT NULL ← se elimina
├── page_title        TEXT       NULL     ← se elimina
├── page_path         TEXT       NULL
├── referrer          TEXT       NULL     ← se elimina
├── utm_*             TEXT       NULL
├── viewport_*        INTEGER    NULL
├── niche             TEXT       NULL
├── ip / country / user_agent / browser / os / device_type
├── cloudfront_meta   JSONB      NULL    ← se elimina
├── event_id          UUID       NULL
├── event_type_id     UUID       NULL (FK event_types.id)
└── event_props       JSONB      NULL

Indices de tracking_events afectados:
- idx_tracking_referrer   (parcial referrer IS NOT NULL)  ← se elimina

contacts
├── id                UUID       PK
├── created_at        TIMESTAMPTZ NOT NULL
├── received_at       TIMESTAMPTZ NOT NULL
├── name / email / message  (CITEXT email)
├── company / role / service_type / budget / timeline / niche
├── ip / country / user_agent
├── cloudfront_meta   JSONB      NULL    ← se elimina
├── status / notes
└── session_id        TEXT       NULL
```

### Despues

```text
tracking_events (PARTITION BY RANGE(created_at))
├── session_id        TEXT       NOT NULL
├── page_id           UUID       NOT NULL
├── created_at        TIMESTAMPTZ NOT NULL
├── received_at       TIMESTAMPTZ NOT NULL
├── page_path         TEXT       NULL
├── utm_*             TEXT       NULL
├── viewport_*        INTEGER    NULL
├── niche             TEXT       NULL
├── ip / country / user_agent / browser / os / device_type
├── event_id          UUID       NULL
├── event_type_id     UUID       NULL (FK event_types.id)
└── event_props       JSONB      NULL

Indices de tracking_events que QUEDAN:
- idx_tracking_session_created
- idx_tracking_created_brin   (BRIN time-series)
- idx_tracking_page_path
- idx_tracking_utm_source     (parcial utm_source IS NOT NULL)
- idx_tracking_country        (parcial country IS NOT NULL)
- idx_tracking_device_type
- idx_tracking_niche_created  (parcial niche IS NOT NULL)
- idx_tracking_event_type

contacts
├── id                UUID       PK
├── created_at        TIMESTAMPTZ NOT NULL
├── received_at       TIMESTAMPTZ NOT NULL
├── name / email / message
├── company / role / service_type / budget / timeline / niche
├── ip / country / user_agent
├── status / notes
└── session_id        TEXT       NULL
```

## 6. Tests Requeridos

### 6.A. TDD flows

`N/A — el cambio es de eliminacion. No hay logica nueva.`

### 6.B. Unit tests (Pytest)

Actualizar tests existentes:

- `test_save_tracking_event_persists_item.py` [AC-5]:
  - **Antes**: `assert payload['page_url'] == ...` y
    `assert payload['expires_at'] is None`.
  - **Despues**: assertions de `not in`:
    - `assert 'expires_at' not in payload`
    - `assert 'cloudfront_meta' not in payload`
    - `assert 'page_url' not in payload`
    - `assert 'page_title' not in payload`
    - `assert 'referrer' not in payload`

- `test_valid_event_persists_e2e.py` (integration) [AC-11]:
  - **Antes**: `assert item['page_url'] == 'https://...'` y
    `assert item['page_title'] == 'Projects'`.
  - **Despues**: eliminar esos asserts (las columnas ya no existen en
    el row de Neon).

Tests que **NO se modifican** y deben seguir verdes:

- `tests/unit/shared/http/test_ip_extractor.py::extract_cloudfront_meta`
  (decision 3 — el helper sigue vivo).
- `tests/unit/shared/lambda_kit/test_http_handler_injects_meta_from_headers.py`
  (decision 3 — la inyeccion sigue activa, asserta
  `'cloudfront_meta': {}` en el `_meta` validado).
- `test_track_model_tracking_payload_excludes_cf_token_and_meta.py`:
  sigue verde, asserta `payload['page_title'] == 'Projects'` PERO sobre
  el dict que devuelve `TrackEventModel.tracking_payload()`, NO sobre el
  `neon_payload`. El Pydantic sigue conteniendo `page_title`; el dropeo
  ocurre downstream.
- `test_handler_returns_400_on_missing_session_id.py`,
  `test_track_model_rejects_missing_session_id.py`,
  `test_track_controller_rejects_invalid_payload.py`: usan `page_url`
  en sus fixtures (campo Pydantic todavia vigente).

### 6.C. Typecheck

- `python -m compileall -q serverless/lambda/services/tracking_pixel/core`
- `python -m compileall -q serverless/lambda/services/contact_form/core`
- `python -m compileall -q serverless/lambda/shared/db`

### 6.D. E2E / Integration (Pytest + DynamoDB local + Neon branch)

- `serverless tests --type=integration --lambda=tracking_pixel` —
  cubre AC-6 (handler `/track` devuelve 204 con headers cloudfront-*).
- `serverless tests --type=integration --lambda=contact_form` —
  cubre AC-7 (handler `/contact` devuelve 201 con headers cloudfront-*).

## 7. Archivos Afectados

### Crear

- `serverless/lambda/shared/db/alembic/versions/<rev>_drop_cloudfront_meta_and_expires_at.py`
  — migracion Alembic con `down_revision = 'b2c3d4e5f6a7'`. `upgrade()`
  hace `op.drop_column` x3; `downgrade()` recrea las 3 columnas vacias.
  - Verificar: en branch Neon de prueba — `alembic upgrade head` +
    `alembic downgrade -1` + `alembic upgrade head` sin errores.
  - Verificar: `serverless run --stage=local --lambda=db
    --event=events/current.json` retorna la nueva revision.

### Modificar

- `serverless/lambda/shared/db/models/tracking.py` [AC-1, AC-3, AC-5]
  — eliminar columnas `expires_at`, `page_url`, `page_title`,
  `referrer`, `cloudfront_meta` y la entrada
  `Index('idx_tracking_referrer', ...)` de `__table_args__`.
  - Verificar: `python -m compileall -q
    serverless/lambda/shared/db/models/`.
  - Verificar: `serverless tests --type=unit --lambda=db` verde.

- `serverless/lambda/shared/db/models/contact.py` [AC-2, AC-6]
  — eliminar `cloudfront_meta` y su comentario.
  - Verificar: idem `compileall` + `serverless tests --type=unit
    --lambda=db`.

- `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py`
  [AC-5, AC-7]
  — eliminar `expires_at`, `page_url`, `page_title`, `referrer` y
  `cloudfront_meta` del dict `neon_payload`; quitar el parametro
  `cloudfront_meta` de `process_tracking_event`; actualizar docstrings
  afectadas.
  - Verificar: `serverless tests --type=unit --lambda=tracking_pixel`.

- `serverless/lambda/services/tracking_pixel/core/controllers/tracking/track.py`
  [AC-5, AC-7]
  — eliminar `cloudfront_meta=meta.cloudfront_meta,` del call al service.
  - Verificar: `serverless tests --type=unit --lambda=tracking_pixel`.

- `serverless/lambda/services/contact_form/core/services/contact_service.py`
  [AC-6, AC-8]
  — eliminar `cloudfront_meta` del dict `neon_payload`.
  - Verificar: `serverless tests --type=unit --lambda=contact_form`.

- `serverless/lambda/services/contact_form/core/models/contact.py`
  [AC-6, AC-8]
  — eliminar el branch que inyecta `cloudfront_meta` en `form_fields()`;
  actualizar docstring.
  - Verificar: `serverless tests --type=unit --lambda=contact_form`.

- `serverless/lambda/services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py`
  [AC-5]
  — reemplazar los asserts de `payload['page_url']` y
  `payload['expires_at'] is None` por asserts `not in` para las 5 keys
  dropeadas.
  - Verificar: `serverless tests --type=unit --lambda=tracking_pixel`.

- `serverless/lambda/services/tracking_pixel/tests/integration/test_valid_event_persists_e2e.py`
  [AC-11]
  — eliminar los asserts de `item['page_url']` y `item['page_title']`.
  - Verificar: `serverless tests --type=integration --lambda=tracking_pixel`.

### Eliminar

- `N/A` — ningun archivo se borra entero (el helper
  `extract_cloudfront_meta` y sus tests permanecen, decision 3).

### Verificar (sin modificar)

- `serverless/lambda/shared/http/ip_extractor.py` — el helper queda.
- `serverless/lambda/shared/lambda_kit/http_dispatch.py` — la inyeccion
  queda.
- `serverless/lambda/services/tracking_pixel/core/models/tracking.py`
  — `TrackEventMeta.cloudfront_meta` queda (Pydantic acepta el dict
  pero ya nadie lo lee).
- `serverless/lambda/shared/tests/unit/shared/http/test_ip_extractor.py`
  — tests permanecen verdes.
- `serverless/lambda/shared/tests/unit/shared/lambda_kit/test_http_handler_injects_meta_from_headers.py`
  — test permanece verde.

---

[← 01-contexto-y-decision.md](01-contexto-y-decision.md) | [03-commits.md →](03-commits.md)
