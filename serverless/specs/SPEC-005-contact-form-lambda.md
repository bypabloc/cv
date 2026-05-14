# SPEC-005: Lambda `contact_form`

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/src/contact_form/`, `serverless/template.yaml`
**Dependencias**: SPEC-002 (common), SPEC-003 (cache), SPEC-004 (rate-limit)
**Paralelizable con**: SPEC-006, SPEC-007

## 1. Contexto

Lambda principal del backend: recibe POST /contact desde el form en el
frontend (los 6 subdominios del portfolio), valida Turnstile contra
Cloudflare, aplica rate-limit per-IP, persiste el contacto en DynamoDB
`contacts` y envia notificacion por SES al owner.

### Hallazgos de exploracion

- Flujo completo documentado en `serverless/ARCHITECTURE.md` seccion 3
- Skills relevantes: `aws-lambda-python`, `cloudflare-turnstile`,
  `aws-ses`, `aws-dynamodb`, `serverless-rate-limit`, `dynamodb-cache`
- Powertools `@idempotent` decorator separado del `@cached` (skill
  `dynamodb-cache` doc 07 explica diferencia)

## 2. Solucion propuesta

Crear `serverless/src/contact_form/` con 7 archivos + templates email:

```text
contact_form/
├── __init__.py
├── handler.py             # lambda_handler con decorators Powertools
├── service.py             # Orquestacion: validate -> persist -> notify
├── turnstile.py           # POST a siteverify + verify hostname/freshness
├── persistence.py         # save_contact(payload) -> contact_id
├── notification.py        # send_owner_email(contact)
├── schemas.py             # Pydantic models input/output + JSON Schema
├── templates/
│   ├── owner_email.html.mjml   # MJML source
│   ├── owner_email.html        # compilado (committed)
│   └── owner_email.txt         # plain-text fallback
└── requirements.txt
```

### Decisiones clave

- **Decision 1: Orden de validaciones** — request validator API GW (shape)
  -> Turnstile (humano vs bot) -> rate-limit (capacidad) -> persist + send.
  Si cualquiera falla, no se persiste el contacto.
- **Decision 2: Powertools `@idempotent`** — hash del body completo,
  almacenado en una tabla idempotency (creada por Powertools auto). Si
  CF reintenta el mismo request (network glitch), no se envia email
  duplicado.
- **Decision 3: MJML para email HTML** — compilado offline via
  `scripts/compile_mjml.mjs`. El runtime Lambda solo lee el .html
  precompilado (no requiere Node). El plain-text se genera en mismo paso.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given POST /contact con body valido y Turnstile token OK,
  When invoco la Lambda, Then retorna 200 con `{"ok": true, "contact_id":
  <UUIDv7>, "message": "Gracias, te respondo en 24-48h"}`
- **AC-2**: Given POST /contact con `cf_token` invalido, When invoco,
  Then retorna 403 con `{"error": "turnstile_failed", "code":
  "<error-code>"}` sin persistir ni enviar email
- **AC-3**: Given mismo IP haciendo POST /contact 4 veces en <5min, When
  4ta invocacion, Then retorna 429 con `{"error":
  "rate_limit_exceeded", "retry_after_seconds": <N>}` sin persistir ni
  enviar email
- **AC-4**: Given POST /contact con body invalido (email malformado,
  message > 2000 chars, falta `name`), When invoco, Then retorna 400
  desde API Gateway request validator (sin invocar Lambda)
- **AC-5**: Given POST /contact valido, When inspecciono DynamoDB
  tabla `contacts`, Then existe item con `id` retornado, `email`, `name`,
  `message`, `service_type`, `created_at`, `ip_address` (CF-Connecting-IP),
  `country` (CF-IPCountry), `turnstile_hostname`
- **AC-6**: Given POST /contact valido, When verifico email del owner
  (Gmail), Then llega en <30s con subject `"Nuevo contacto: <name> via
  <subdomain>"`, body HTML formateado (tables-based) y plain-text fallback
- **AC-7**: Given POST /contact valido + retry con mismo body en <1min,
  When invoco 2da vez, Then NO se envia segundo email (idempotency
  Powertools previene duplicado)

## 4. Diagrama de Flujo

Documentado en `serverless/ARCHITECTURE.md` seccion 3. Reproducir
solo el bloque del handler:

```text
event POST /contact
    |
    v
JSON Schema validator (API GW) -> 400 si invalido
    |
    v
@idempotent(persistence_store=DynamoDBPersistenceLayer) hash body
    |
    v
@logger.inject_lambda_context + @tracer + @metrics
    |
    v
1. extract_ip(event)
2. validate_turnstile(token, ip) -> 403 si falla
3. check_or_raise(ip, '/contact', country, turnstile_validated=True) -> 429
4. save_contact(payload) -> contact_id
5. send_owner_email(contact)
    |
    v
return 200 {ok, contact_id, message}
```

## 5. Diagrama ER

Tabla `contacts` (DynamoDB) y `idempotency` (Powertools auto). Schema en
`serverless/ARCHITECTURE.md` seccion 6.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN body valido + token OK THEN 200 + contact_id [AC-1]
- WHEN token invalido THEN 403, no persist, no email [AC-2]
- WHEN 4 requests en 5min THEN 4ta = 429 [AC-3]
- WHEN body invalido (email malformed) THEN API GW 400 antes de Lambda [AC-4]
- WHEN valido THEN row en DynamoDB con campos esperados [AC-5]
- WHEN valido THEN email llega con shape correcto [AC-6]
- WHEN mismo body 2 veces THEN solo 1 email enviado [AC-7]

### 6.B. Unit Tests

Path mirror `tests/unit/contact_form/test_<X>.py`:

- `test_handler.py` — handler con event mock + moto DynamoDB + responses (httpx mock)
- `test_service.py` — orquestacion entre componentes
- `test_turnstile.py` — siteverify mocked con responses, verifica
  hostname check + challenge_ts freshness
- `test_persistence.py` — put_item con ConditionExpression idempotente
- `test_notification.py` — send_email con moto SES, verifica plain+html
- `test_schemas.py` — pydantic models validan correctos + rechazan invalidos

Coverage minimo: 85% per-file.

### 6.D. E2E (Playwright extiende suite existente)

- E2E test contra dev stack: form submit real desde Playwright a
  https://api-dev.the-full-stack.com/contact con Turnstile MOCK_PASS
  token + verifica response 200 + email llega a inbox de test.

## 7. Archivos Afectados

### Crear

- `serverless/src/contact_form/handler.py` — entry point
  - Verificar: AC-1 a AC-7 + sam local invoke con event JSON
- `serverless/src/contact_form/service.py` — orquestacion
- `serverless/src/contact_form/turnstile.py` — siteverify
  - Verificar: tests con responses mock + dominios whitelist
- `serverless/src/contact_form/persistence.py` — put_item
- `serverless/src/contact_form/notification.py` — send_email
- `serverless/src/contact_form/schemas.py` — Pydantic models + JSON Schema export
- `serverless/src/contact_form/templates/owner_email.html.mjml` — MJML source
- `serverless/src/contact_form/templates/owner_email.html` — compilado
- `serverless/src/contact_form/templates/owner_email.txt` — plain text
- `serverless/src/contact_form/requirements.txt` — sin deps extra (todo via Layer)
- `serverless/events/contact_form_valid.json` — sample API GW event
- `serverless/events/contact_form_invalid_token.json`
- `serverless/events/contact_form_missing_email.json`
- `serverless/events/contact_form_throttled.json`

### Modificar

- `serverless/template.yaml` — agregar `ContactFormFunction` con:
  - Policies: DynamoDBWritePolicy contacts + rate_limit_buckets +
    DynamoDBReadPolicy rate_limit_rules + cache CRUD + ses:SendEmail
    + ssm:GetParameter + kms:Decrypt
  - ReservedConcurrentExecutions: 5
  - Environment vars: CONTACTS_TABLE, CACHE_TABLE, RATE_LIMIT_*, OWNER_EMAIL,
    POWERTOOLS_IDEMPOTENCY_TABLE
  - Events: ContactPost API
- `serverless/template.yaml` — agregar `IdempotencyTable` (Powertools
  required, PK=id S, TTL=expires_at)

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | schemas.py + templates/ | — | T2, T3, T4 |
| T2 | turnstile.py + tests | T1 | T3, T4 |
| T3 | persistence.py + tests | T1 | T2, T4 |
| T4 | notification.py + tests + MJML compile | T1 | T2, T3 |
| T5 | service.py (orquesta) | T2, T3, T4 | T6 |
| T6 | handler.py + idempotency wiring | T5 | — |
| T7 | template.yaml updates + deploy | T6 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-002, SPEC-003, SPEC-004 done
- [ ] SES production access aprobado (SPEC-011) o usar SES Sandbox con
      email verificado para testing
- [ ] Turnstile widget creado con sitekey publico

### Definition of Done

- [ ] AC-1 a AC-7 cumplidos
- [ ] Coverage >= 85% per-file
- [ ] sam local invoke con 4 events JSON ejecuta correctamente
- [ ] Smoke test: curl POST /contact desde local pasa contra stage dev
- [ ] Latencia cold start < 1.5s, warm < 500ms
- [ ] CloudWatch Logs primera invocacion sin errores
- [ ] Email recibido en Gmail pasa Mail Tester score >= 8/10
