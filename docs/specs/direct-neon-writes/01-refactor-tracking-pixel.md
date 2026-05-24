# Phase 1: refactor tracking_pixel a escritura directa a Neon

> Reemplazar el write a DDB `tracking` por un INSERT en Neon
> `tracking_events_default`. Mantener Turnstile + rate-limit + cache
> (esos siguen usando DDB y SSM). Idempotencia via `ON CONFLICT
> (session_id, event_id) DO NOTHING`.

[Volver al README](README.md)

## Archivos afectados

### Modificar

- `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py`
  - Reemplazar `dynamodb.PutItem` por `insert_tracking(session, payload)` del repository
  - Construir el `payload` desde el `TrackModel` validado (con `received_at=datetime.utcnow()`, defaults igual que hoy)
  - Mantener el call a `cache`, `rate-limit-*` (siguen siendo DDB)
  - Verificar: `serverless tests --type=unit --lambda=tracking_pixel`
- `serverless/lambda/services/tracking_pixel/manifest.yaml`
  - `uses.tables`: remover `tracking: read-write` (queda `cache`, `rate-limit-rules`, `rate-limit-buckets`)
  - `uses.secrets`: agregar `neon-url`
  - Verificar: `python devtools/run.py serverless lint-deps --lambda=tracking_pixel`
- `serverless/lambda/services/tracking_pixel/pyproject.toml`
  - Si esta declarando `boto3` y ya no se usa para DDB write, se queda igual (cache y rate-limit lo usan)
  - Agregar dependencia de `psycopg[binary]` si no esta heredada del closure de `shared.db`
- `serverless/lambda/services/tracking_pixel/tests/unit/test_tracking_service_*.py`
  - Mock de `insert_tracking` (no de boto3 DynamoDB)
  - Asserts EXACTOS del payload pasado al repository
  - Verificar: pytest verde
- `serverless/lambda/services/tracking_pixel/tests/integration/_fixtures/db.py` (NUEVO si no existe)
  - sqlite fixture compatible con el modelo `TrackingEvent`
  - Verificar: integration tests verdes contra sqlite

### Conservar (sin cambios)

- `handler.py` — sigue siendo `http_handler` generico
- `controllers/track/create.py` — sigue orquestando (validate -> service -> normalize)
- `models/track.py` — Pydantic schema sin cambios
- `settings/config.py` — `AppConfig` sin cambios
- `settings/operations.py` — sin cambios

## Tests requeridos

### 6.A TDD (escribir antes de implementar)

- **T-1.1** WHEN insert_tracking recibe un payload valido THEN devuelve `True` y crea 1 fila [AC-1]
- **T-1.2** WHEN insert_tracking recibe el mismo `(session_id, event_id)` 2x THEN la 2a llamada devuelve `False` y no crea duplicado [AC-3]
- **T-1.3** WHEN tracking_service ejecuta con un TrackModel valido THEN llama a insert_tracking con el payload correcto [AC-1]

### 6.B Unit (Vitest no aplica — pytest)

- `test_tracking_service_persists_to_neon.py` — mockea insert_tracking, verifica payload exacto
- `test_tracking_service_handles_duplicate.py` — insert_tracking devuelve False, el service retorna 200 igual

### 6.C Integration

- `test_track_e2e_inserts_neon_row.py` — sqlite in-memory, llama al handler, verifica fila en `tracking_events_default`
- `test_track_e2e_idempotent.py` — 2 POSTs identicos, 1 fila resultante

## Verificacion incremental

```bash
# Antes de commitear:
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
python devtools/run.py serverless tests --type=integration --lambda=tracking_pixel
python devtools/run.py serverless lint-deps --lambda=tracking_pixel
python -m compileall -q serverless/lambda/services/tracking_pixel/core
```

## Done cuando

- [ ] T-1.1, T-1.2, T-1.3 verdes
- [ ] Suite unit + integration verde (>= 80% coverage en archivos modificados)
- [ ] Manifest validado por `lint-deps`
- [ ] `core.handler` arranca sin imports rotos (`compileall` OK)
