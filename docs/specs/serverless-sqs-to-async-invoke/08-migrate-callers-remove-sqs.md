# 08 — Migrar auth/users a send_email + eliminar SQS

[← 07 cv cache](07-cv-cache.md) · [siguiente: 09 cleanup stream_processor →](09-cleanup-stream-processor.md)

> Fase 6. `auth` y `users` dejan de publicar a SQS y pasan a invocar
> `send_email` async. Se eliminan las 3 colas SQS + DLQ + `shared.queue`. De los
> 3 workers: `auth_email_worker` y `contact_worker` se **borran**;
> `tracking_worker` ya se **reconvirtió** a `tracking_writer` (invoke-target) en
> la fase 4 — NO se borra.

## 8.1 Migrar `auth` y `users`

### auth (`email_dispatch_service.py`)
- Hoy: `_publish` arma `{kind, to, user_id, niche, subject_id, data}` y llama
  `send_to_queue('auth-email', payload)`.
- Cambio: reemplazar por
  `invoke_async('send_email', {operation:'email', action:'send', data:{kind, to, data}})`
  via `from shared.aws.lambda_invoke import invoke_async`.
- El payload del email pasa a `{kind, to, data}` (lo que `send_email` espera).
- `manifest.yaml` de auth: quitar `uses.queues`, agregar `uses.invokes:
  [send_email]`.

### users (`email_dispatch_service.py`)
- Idéntico patrón. Mismos kinds que el worker manejaba. `manifest.yaml` igual.

## 8.2 Eliminar colas SQS + `shared.queue` + 2 workers

- Borrar `serverless/lambda/services/auth_email_worker/` (su trabajo lo hace
  `send_email`).
- Borrar `serverless/lambda/services/contact_worker/` (contact_form escribe
  inline ahora).
- **NO borrar `tracking_worker`**: ya es `tracking_writer` (fase 4, archivo 06).
- Borrar `serverless/lambda/shared/queue/`.
- Borrar `serverless/lambda/resources/sqs/`.
- `serverless destroy` de las colas + DLQ + de los 2 workers borrados, por
  stage (dev/stage/prod) — son recursos AWS reales, no sólo código.
- Limpiar `pyproject.toml` de auth/users/contact_form/tracking_pixel: quitar la
  dep de `shared.queue` si la declaran.

## 8.3 Reglas

- **SIEMPRE** el payload del invoke matchea el contrato de `send_email`.
- **SIEMPRE** `destroy` de los recursos AWS (colas, DLQ, funciones worker
  borradas) por stage, no sólo borrar el código.
- **NUNCA** queda un `send_to_queue` ni un `Records[]` handler de SQS.

## Archivos afectados (fase 6)

### Eliminar
- `serverless/lambda/services/auth_email_worker/`
- `serverless/lambda/services/contact_worker/`
- `serverless/lambda/shared/queue/`
- `serverless/lambda/resources/sqs/`

### Modificar
- `serverless/lambda/services/auth/core/services/email_dispatch_service.py` +
  `auth/manifest.yaml` + `auth/pyproject.toml`
  - Verificar: `serverless tests --type=unit --lambda=auth` + `lint-deps`
- `serverless/lambda/services/users/core/services/email_dispatch_service.py` +
  `users/manifest.yaml` + `users/pyproject.toml`
  - Verificar: `serverless tests --type=unit --lambda=users` + `lint-deps`

### Destruir (AWS, por stage)
- 3 colas SQS + 3 DLQ; funciones `auth_email_worker` + `contact_worker`.
  - Verificar: `serverless destroy --lambda=auth_email_worker --stage=<X>` etc.;
    `aws sqs list-queues` no lista las colas; `lint-deps` global verde.

[← 07 cv cache](07-cv-cache.md) · [siguiente: 09 cleanup stream_processor →](09-cleanup-stream-processor.md)
