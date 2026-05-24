# Phase 2: refactor contact_form a escritura directa a Neon

> Reemplazar el write a DDB `contacts` por un INSERT en Neon `contacts`.
> Mantener Turnstile, rate-limit, cache (DDB) y el envio de email (SES).
> Idempotencia via `idempotency_key` -> `contacts.id` con `ON CONFLICT
> (id) DO NOTHING`.

[Volver al README](README.md)

## Archivos afectados

### Modificar

- `serverless/lambda/services/contact_form/core/services/contact_service.py`
  - Reemplazar `dynamodb.PutItem` por `insert_contact(session, payload)`
  - Generar `id = uuid7()` o usar `payload.idempotency_key` si viene (validacion: UUID v7)
  - Mantener el flujo Turnstile -> rate-limit -> insert -> SES
  - Verificar: `serverless tests --type=unit --lambda=contact_form`
- `serverless/lambda/services/contact_form/manifest.yaml`
  - `uses.tables`: remover `contacts: read-write` (quedan `cache`, `rate-limit-rules`, `rate-limit-buckets`)
  - `uses.secrets`: agregar `neon-url`
  - Verificar: `serverless lint-deps --lambda=contact_form`
- `serverless/lambda/services/contact_form/core/models/contact.py`
  - Agregar campo opcional `idempotency_key: UUID | None = None` al `ContactModel`
  - Validar formato UUID v7 si viene
- `serverless/lambda/services/contact_form/pyproject.toml`
  - Agregar `psycopg[binary]` si no esta heredada del closure de `shared.db`
- `serverless/lambda/services/contact_form/tests/unit/test_contact_service_*.py`
  - Mock de `insert_contact`, no de boto3 DynamoDB
  - Test idempotencia con mismo `idempotency_key`

### Conservar

- `handler.py` — `http_handler` generico
- `controllers/contact/create.py` — orquesta validate -> Turnstile -> rate-limit -> insert -> SES
- `settings/config.py`, `settings/operations.py`
- `templates/` — el email HTML/MJML

## Tests requeridos

### 6.A TDD

- **T-2.1** WHEN insert_contact recibe payload valido con `id` nuevo THEN crea 1 fila + devuelve True [AC-2]
- **T-2.2** WHEN insert_contact recibe el mismo `id` 2x THEN la 2a devuelve False sin crear duplicado [AC-3]
- **T-2.3** WHEN contact_service procesa con `idempotency_key` valido THEN usa ese valor como `contacts.id` [AC-3]
- **T-2.4** WHEN contact_service procesa sin `idempotency_key` THEN genera uno con uuid7() [AC-2]

### 6.B Unit

- `test_contact_service_persists_to_neon.py`
- `test_contact_service_uses_idempotency_key_when_provided.py`
- `test_contact_service_generates_uuid7_when_no_key.py`
- `test_contact_service_sends_email_after_insert.py` (SES se llama solo si insert fue exitoso, no si fue ON CONFLICT skip)

### 6.C Integration

- `test_contact_e2e_inserts_neon_and_sends_email.py` (mock SES SendEmail)
- `test_contact_e2e_idempotent_no_duplicate_email.py` (mismo idempotency_key 2x: 1 fila, 1 email)

## Decision: email idempotente

Si `insert_contact` retorna `False` (conflict — duplicado por `idempotency_key`), NO se envia email. Asi un retry del cliente no genera 2 emails al owner.

## Verificacion incremental

```bash
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=integration --lambda=contact_form
python devtools/run.py serverless lint-deps --lambda=contact_form
python -m compileall -q serverless/lambda/services/contact_form/core
```

## Done cuando

- [ ] T-2.1 a T-2.4 verdes
- [ ] Suite unit + integration verde (>= 80% coverage en archivos modificados)
- [ ] Email no se envia 2 veces ante reintento con mismo `idempotency_key`
- [ ] `lint-deps` verde
