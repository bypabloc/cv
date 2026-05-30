# 06 — Migrar auth/users a send_email + borrar SQS y workers

[← 05 encoders](05-encoders-refactor.md) · [siguiente: 07 cleanup →](07-cleanup-stream-processor.md)

> Fase 5. Reapunta `auth` y `users` a invocar `send_email` async (en vez de
> publicar a SQS), y borra los 3 workers + `shared.queue` + `resources/sqs/`.
> (`contact_form` y `tracking_pixel` ya se migraron en la fase 4 / archivo
> 05.) Esta fase es secuencial tras la 4: borrar `shared.queue` antes de
> migrar los callers rompería imports.

## 6.1 `auth` → invoca `send_email`

- `auth/core/services/email_dispatch_service.py`:
  - Quitar `from shared.queue.publisher import send_to_queue`.
  - `_publish(kind, to, user_id, niche, data)` → construir el payload
    `{operation:'email', action:'send', data:{kind, to:[to], data}}` e invocar
    `invoke_async(function_name=os.environ['LAMBDA_SEND_EMAIL_FUNCTION_NAME'],
    payload=...)`. Import: `from shared.aws.lambda_invoke import invoke_async`.
  - Quitar `subject_id` del payload (lo resuelve `send_email` desde
    `email-config`). `publish_magic_link`/`publish_code` mantienen su firma.
- `auth/manifest.yaml`: −`uses.queues`; +`uses.invokes: [send_email]`.
  `sends-email` queda `false`. `auth` SIGUE escribiendo Neon síncrono
  (sin cambios en repositories).
- Call sites read-only (no cambian): `register/start.py`, `login/start.py`,
  `verify/resend_code.py`.

## 6.2 `users` → invoca `send_email`

- `users/core/services/email_dispatch_service.py`: igual que auth para sus 4
  kinds (`email-change-verify`, `email-changed`, `account-disabled`,
  `account-deleted`). Quitar `_subject_id` + `send_to_queue`.
- `users/manifest.yaml`: −`uses.queues`; +`uses.invokes: [send_email]`.

## 6.3 Borrar SQS + workers + shared.queue

### Eliminar (dirs/archivos completos)
- `serverless/lambda/services/auth_email_worker/` (completo)
- `serverless/lambda/services/contact_worker/` (completo)
- `serverless/lambda/services/tracking_worker/` (completo)
- `serverless/lambda/shared/queue/` (completo: publisher.py, client.py,
  `__init__.py`, pyproject.toml, tests/)
- `serverless/lambda/resources/sqs/` (completo: 6 yaml + README.md)

### Modificar (pyproject.toml: quitar comentarios/deps de shared.queue)
- `auth/pyproject.toml`, `contact_form/pyproject.toml`,
  `tracking_pixel/pyproject.toml`, `users/pyproject.toml`.

### Destruir en AWS (operación, en deploy de fase 7)
- `serverless destroy --lambda=auth_email_worker --stage=<X>` (×3 workers).
- Borrar las colas/DLQ (`aws sqs delete-queue`) una vez; al quitar los yaml,
  `infra_provision` no las recrea.

## 6.4 Reglas
- **SIEMPRE** el invoke de send_email se degrada a log si falla (best-effort).
- **NUNCA** queda un import de `shared.queue`.

## Archivos afectados (fase 5) — resumen

### Modificar
- `auth/{core/services/email_dispatch_service.py, manifest.yaml, pyproject.toml}`
  - Verificar: `serverless tests --type=unit --lambda=auth` + `lint-deps --lambda=auth`
- `users/{core/services/email_dispatch_service.py, manifest.yaml, pyproject.toml}`
  - Verificar: `serverless tests --type=unit --lambda=users` + `lint-deps --lambda=users`
- `contact_form/pyproject.toml`, `tracking_pixel/pyproject.toml` (limpieza shared.queue)

### Eliminar
- 3 workers + `shared/queue/` + `resources/sqs/` (ver §6.3).
  - Verificar: `serverless tests --type=unit` (suite completa) + `lint-deps`
    + `rg "shared.queue|ASYNC_MODE"` → 0.

[← 05 encoders](05-encoders-refactor.md) · [siguiente: 07 cleanup →](07-cleanup-stream-processor.md)
