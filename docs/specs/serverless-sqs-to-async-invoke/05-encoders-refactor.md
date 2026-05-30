# 05 — Encoders: quitar ASYNC_MODE + escritura inline síncrona

[← 04 send_email](04-send-email-lambda.md) · [siguiente: 06 migrar auth/users →](06-migrate-callers-remove-sqs.md)

> Fase 4. `contact_form` y `tracking_pixel` dejan de ser encoders SQS:
> escriben a Neon **inline y síncrono** (psycopg3 vía `shared.db`, pooled,
> `warm_db()` en INIT para SnapStart) y se elimina el flag `ASYNC_MODE` + el
> path sync legacy duplicado. NO se crea `db_writer`. `contact_form` además
> invoca `send_email` async para el owner.

## 5.1 `contact_form`

### `core/settings/config.py`
- Eliminar `async_mode` + su doc (líneas ~131-138).

### `core/handler.py`
- `success_status` SIEMPRE **201** (quitar el condicional 202/201 por
  `AppConfig.async_mode`).

### `core/controllers/contact/create.py`
- Eliminar el branch por `AppConfig.async_mode` y los métodos `_execute_async`
  (SQS) y `_execute_sync` (legacy). El cuerpo de `execute()` queda como flujo
  único:
  1. rate-limit (`check_or_raise`) — igual.
  2. Turnstile (`verify_captcha_or_bypass`) — igual.
  3. resolver `session_id` + `origin_niche` — igual.
  4. pre-generar `contact_id` (UUIDv7) + `created_at`.
  5. **escribir contacto a Neon síncrono** (`save_contact` del service:
     `ensure_session_and_visit` + INSERT idempotente `ON CONFLICT (id)`).
  6. **invocar `send_email` async** (`InvocationType='Event'`,
     `kind=contact`, `to=owner_emails`, `data=form_fields`,
     `reply_to=[email]`). Degrada a log si falla (no rompe el 201).
  7. `_auto_blacklist_step` — igual.
  8. responder 201 con `ContactCreatedOutput` (contacto persistido).
- Importa el invoke vía `from shared.aws.lambda_invoke import invoke_async` +
  `os.environ['LAMBDA_SEND_EMAIL_FUNCTION_NAME']`.

### `core/services/contact_service.py`
- Eliminar `enqueue_contact_message` (SQS) + el import `send_to_queue` +
  `QueuePublishError`.
- Conservar/limpiar `save_contact` (la escritura Neon) — quitar de ahí el
  envío SES directo (lo hace `send_email` ahora). El render mustache-lite y
  `send_owner_email` se ELIMINAN (el email lo arma `send_email` con Jinja2).
- `owner_emails`: `get_secret_by_name('owner-email')` (se conserva el secret).

### `manifest.yaml`
- −`uses.queues`; +`uses.invokes: [send_email]`.
- `uses.secrets`: conservar `turnstile-secret`, `turnstile-bypass-public-key`,
  `owner-email`, `neon-url`. Quitar `ses-from-address` (ya no manda SES
  directo; lo hace send_email).
- `uses.tables`: `cache`, `rate-limit-rules`, `rate-limit-buckets` (igual).
- `sends-email`: **false** (manda vía send_email).
- `env`: eliminar `ASYNC_MODE` de los 4 bloques.
- `memory`: ya es 256 (footprint Neon) — se mantiene; MEDIR.
- `snap_start: true` — se mantiene (clave para el cold).

## 5.2 `tracking_pixel`

### `core/settings/config.py`
- Eliminar `async_mode`.

### `core/controllers/tracking/track.py`
- Eliminar branch + `_execute_async` (SQS) y `_execute_sync`. Flujo único:
  1. rate-limit — igual.
  2. pre-generar `page_id` (UUIDv7) + `created_at`.
  3. **escribir tracking_event a Neon síncrono** (parse UA +
     `ensure_session_and_visit` + INSERT idempotente
     `ON CONFLICT (created_at, visit_id, page_id)`).
  4. responder **202** (`sendBeacon` no espera).

### `core/services/tracking_service.py`
- Eliminar `enqueue_tracking_message` (SQS) + import `send_to_queue`.
- El path sync legacy (`process_tracking_event`, `parse_user_agent`,
  `_ensure_db_deps`) pasa a ser el ÚNICO path. **Ahora `shared.db` es
  incondicional** → import al TOP (no lazy) + `warm_db()` en INIT. El
  `_ensure_db_deps` lazy-hack se elimina (ya no hay path que no use Neon).
- `parse_user_agent` (ua_parser) se conserva (era del worker; ahora inline).

### `core/models/tracking.py`
- Quitar refs a `ASYNC_MODE` si las hay.

### `manifest.yaml` — TRADEOFF DE MEMORIA
- −`uses.queues`; SIN `uses.invokes` (tracking no manda email).
- `uses.secrets`: conservar `neon-url`.
- `uses.tables`: `cache` (UA cache), `rate-limit-rules`,
  `rate-limit-buckets`.
- `env`: eliminar `ASYNC_MODE`.
- **`memory: 128 → 256`**: ahora importa `shared.db` (sqlalchemy) en cada
  invocación. Por `lambda-config.md`, ningún Lambda con `shared.db` baja de
  256 MB (footprint ~117-127 MB a 128 = OOM). Es una **regresión aceptada**
  a cambio de eliminar el worker. Documentar la medición en el comentario.
- `snap_start: true` — se mantiene.
- Agregar `warm_db()` en INIT del handler (como los otros Lambdas Neon) +
  `import shared.db.models.<dominios usados>` para que las FK resuelvan.

### Mitigación opcional (NO construir sin medir)
Si la medición de fase 7 muestra que 256 MB / el restore de SnapStart con
sqlalchemy es un problema para `/track` (alto volumen): evaluar un **write
path raw psycopg3** en `shared.db` (sin ORM) — más liviano de importar (la
investigación lo recomendó para escrituras simples). Es un mecanismo paralelo
al `shared.db.repository` (sqlalchemy); sólo se justifica con números. Default:
reusar `shared.db.repository` (consistente, testeado).

## 5.3 Tests

- contact_form: eliminar/portar los tests de `ASYNC_MODE`/202-vs-201/sync
  legacy (`test_handler_returns_201_*`,
  `test_async_mode_does_not_call_send_email`,
  `test_handler_returns_202_with_contact_id_in_async_mode`,
  `test_handler_returns_201_in_sync_mode_legacy`,
  `test_enqueue_failure_returns_500`, `test_rate_limit_failure_does_not_enqueue`,
  `test_turnstile_failure_does_not_enqueue`). Nuevos: el flujo único escribe
  Neon (mock repository) + invoca send_email (mock `invoke_async`) + 201.
- tracking_pixel: idem (`test_handler_returns_204_*`,
  `test_async_mode_does_not_call_neon`, `test_encoder_does_not_parse_user_agent`,
  `test_handler_returns_202_with_page_id_in_async_mode`,
  `test_enqueue_failure_returns_error`). Nuevos: escribe Neon inline (mock) +
  parse UA + 202.

## 5.4 Reglas
- **SIEMPRE** el invoke de send_email se degrada a log si falla (best-effort):
  el 201/202 sale igual. NUNCA rompe el request.
- **SIEMPRE** rate-limit + Turnstile + bot-detection se conservan, mismo orden.
- **NUNCA** queda un import de `shared.queue` ni una ref a `ASYNC_MODE`.
- **NUNCA** se crea `db_writer` ni un segundo invoke para la escritura.

## Archivos afectados (fase 4)

### Modificar
- `contact_form/{core/settings/config.py, core/handler.py,
  core/controllers/contact/create.py, core/services/contact_service.py,
  manifest.yaml}` + tests
- `tracking_pixel/{core/settings/config.py, core/controllers/tracking/track.py,
  core/services/tracking_service.py, core/models/tracking.py, manifest.yaml,
  core/handler.py (warm_db en INIT)}` + tests
  - Verificar (cada uno): `serverless tests --type=unit --lambda=<X>` (≥80%)
    + `serverless lint-deps --lambda=<X>` exit 0

[← 04 send_email](04-send-email-lambda.md) · [siguiente: 06 migrar auth/users →](06-migrate-callers-remove-sqs.md)
