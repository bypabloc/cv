# 04. Infraestructura — DynamoDB + SSM + SQS + IAM

## Resumen

| Recurso | Archivo (resources/...) | Que es | Quien lo lee |
|---------|------------------------|--------|--------------|
| DynamoDB `portfolio-jwt-blacklist-${stage}` | `dynamodb/jwt-blacklist.yaml` | Blacklist de JWTs (temp/access/refresh) con TTL=exp | Lambda `auth` |
| DynamoDB `portfolio-auth-codes-${stage}` | `dynamodb/auth-codes.yaml` | Cache O(1) de codes activos (espejo de auth_email_codes) | Lambda `auth` |
| SSM `/portfolio/${stage}/jwt-secret` | `resources/secrets/jwt-secret.yaml` | SecureString + KMS, secret del HS256 | Lambdas `auth`, futuro `users` |
| SQS `portfolio-auth-email-${stage}` | `sqs/auth-email-queue.yaml` | Cola de emails a enviar (magic-link, code, ...) | productor: `auth`; consumidor: `auth_email_worker` |
| SQS DLQ `portfolio-auth-email-dlq-${stage}` | `sqs/auth-email-dlq.yaml` | DLQ de la cola anterior | n/a |
| Rate-limit rules (data en tabla existente) | seed via `serverless rate-limit set ...` | 5 reglas: register.start/login.start/verify.*/session.refresh/session.logout | Lambda `auth` (via shared.rate_limit) |

NO se crea API Gateway nuevo. Se reusa `portfolio-api` existente. Las
rutas `/auth` y (plan 3) `/users` se agregan automaticamente por
devtools provisioner a partir del `manifest.yaml` de cada Lambda.

## 1. DynamoDB — `portfolio-jwt-blacklist-${stage}`

`serverless/lambda/resources/dynamodb/jwt-blacklist.yaml`:

```yaml
kind: dynamodb-table
name: portfolio-jwt-blacklist-${stage}
billing_mode: PAY_PER_REQUEST
hash_key:
  name: jti
  type: S
range_key: null
stream: null
ttl_attribute: exp
encryption: true
publishes_ssm:
  name: /portfolio/${stage}/dynamodb/jwt-blacklist/name
  arn: /portfolio/${stage}/dynamodb/jwt-blacklist/arn
tags:
  Project: portfolio
  Module: auth
  ManagedBy: devtools
```

**Schema de item**:

```jsonc
{
  "jti": "01H9X...uuid",         // PK (UUID v7 string)
  "user_id": "01H9V...",          // sort no, solo atributo
  "typ": "access",                // 'temp'|'access'|'refresh'
  "family_id": "01H9W...",        // solo si typ=refresh
  "revoked_at": 1717000000,       // unix
  "reason": "logout",             // 'logout'|'rotation'|'reuse'|'forced'
  "exp": 1717003600               // unix; TTL attribute, AWS borra el item
}
```

**Operaciones**:
- `PutItem` cuando se blacklistea un JWT (incl. rotacion de refresh).
- `GetItem` por `jti` en cada request protegida (verificacion).
- `Query` por `family_id` cuando se detecta reuso (requiere GSI; ver
  abajo).

**GSI `by_family_id`** (necesario para AC-8 token reuse detection):

```yaml
hash_key:
  name: jti
  type: S
global_secondary_indexes:
  - name: by_family_id
    hash_key:
      name: family_id
      type: S
    projection: KEYS_ONLY  # ahorra storage; solo necesitamos jti para borrar
```

Aclaracion: el GSI agrega ~2x write cost en items con `family_id`
(refresh JWTs). En el modo PAY_PER_REQUEST esto es marginal a escala
portfolio.

## 2. DynamoDB — `portfolio-auth-codes-${stage}`

`serverless/lambda/resources/dynamodb/auth-codes.yaml`:

```yaml
kind: dynamodb-table
name: portfolio-auth-codes-${stage}
billing_mode: PAY_PER_REQUEST
hash_key:
  name: pk
  type: S
range_key: null
stream: null
ttl_attribute: expires_at
encryption: true
publishes_ssm:
  name: /portfolio/${stage}/dynamodb/auth-codes/name
  arn: /portfolio/${stage}/dynamodb/auth-codes/arn
tags:
  Project: portfolio
  Module: auth
  ManagedBy: devtools
```

**Schema de item**:

```jsonc
{
  "pk": "register#01H9V...",      // PK (formato '<kind>#<user_id>')
  "code_hash_b64": "...",         // SHA-256 b64
  "attempts": 0,
  "created_at": 1717000000,
  "expires_at": 1717000900,       // TTL attribute
  "neon_id": "01H9X..."           // referencia al row de Neon
}
```

**Justificacion del doble store (Neon + DynamoDB)**:
- Neon es la fuente de verdad y la auditoria (queries por user, por
  kind, historial).
- DynamoDB da lookup O(1) por `pk` en cada `verify-code` request sin
  pagar latencia de Neon (~10-30ms a Neon Pooler us-east-1).
- Cuando se inserta un code, el handler escribe ambos en paralelo. Si
  Neon falla, abortamos toda la operacion. Si DynamoDB falla pero Neon
  exito -> log warning, fallback a Neon en verify (degrada
  graciosamente, ~10ms peor).

## 3. SSM — `/portfolio/${stage}/jwt-secret`

`serverless/lambda/resources/secrets/jwt-secret.yaml`:

```yaml
short_name: jwt-secret
description: HS256 secret for JWT signing/verification (auth + users lambdas)
type: SecureString
kms_key: alias/portfolio-lambdas
ssm_path: /portfolio/${stage}/jwt-secret
source_env_var: JWT_SECRET            # docker/env/server/.{stage}
local_env_var: JWT_SECRET             # mismo nombre en local
rotation_interval_days: 90
consumers:
  - lambda: auth
  - lambda: users        # futuro plan 3
```

**Generacion del valor**: 64 bytes random b64url:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Pegar en `docker/env/server/.{dev,stage,prod}` como
`JWT_SECRET=<valor>`. Sincronizar a SSM con:

```bash
python devtools/run.py serverless sync-secrets --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless sync-secrets --stage=stage --aws-profile=tfs-dev
python devtools/run.py serverless sync-secrets --stage=prod --aws-profile=tfs-dev
```

**Rotacion**: cambiar el valor en `docker/env/server/.{stage}` + sync.
Efecto: todos los JWTs vivos quedan invalidos (signature mismatch) y
los users deben re-loguear. NO hacer en horario de uso real.

## 4. SQS — `portfolio-auth-email-${stage}` + DLQ

`serverless/lambda/resources/sqs/auth-email-queue.yaml`:

```yaml
kind: sqs-queue
name: portfolio-auth-email-${stage}
message_retention_seconds: 345600      # 4 dias
visibility_timeout_seconds: 180        # 6x el timeout del worker (30s)
redrive_policy:
  target: portfolio-auth-email-dlq-${stage}
  max_receive_count: 3
publishes_ssm:
  arn: /portfolio/${stage}/sqs/auth-email/arn
  url: /portfolio/${stage}/sqs/auth-email/url
tags:
  Project: portfolio
  Module: auth
  ManagedBy: devtools
```

`serverless/lambda/resources/sqs/auth-email-dlq.yaml`:

```yaml
kind: sqs-queue
name: portfolio-auth-email-dlq-${stage}
message_retention_seconds: 1209600     # 14 dias (DLQ guarda mas)
visibility_timeout_seconds: 30
publishes_ssm:
  arn: /portfolio/${stage}/sqs/auth-email-dlq/arn
  url: /portfolio/${stage}/sqs/auth-email-dlq/url
tags:
  Project: portfolio
  Module: auth
  ManagedBy: devtools
```

**Schema del mensaje** (JSON en el body):

```jsonc
{
  "kind": "register-magic-link",   // 'register-magic-link'|'register-code'|'login-magic-link'|'login-code'|'password-reset'
  "to": "user@example.com",
  "user_id": "01H9V...",
  "niche": "fintech",              // opcional, para template branding
  "subject_id": "auth.register.magic-link.subject",  // i18n key
  "data": {
    "token": "abc...",             // SOLO para magic-link
    "code": "ABCD2345",            // SOLO para code
    "expires_in_min": 15,
    "verify_url": "https://api..." // SOLO para magic-link, ya construida
  },
  "audit_event_id": "01H9Y..."     // para correlacionar con auth_audit_log
}
```

## 5. Lambda `auth_email_worker` (manifest)

`serverless/lambda/services/auth_email_worker/manifest.yaml`:

```yaml
name: auth-email-worker
trigger:
  type: sqs
  queue: portfolio-auth-email-${stage}
  batch_size: 1
  function_response_types:
    - ReportBatchItemFailures
runtime: python3.13
handler: core.handler.lambda_handler
memory: 384
timeout: 30
uses:
  queues:
    - name: portfolio-auth-email-${stage}
      access: consumer
  tables: {}
  secrets:
    - ses-from-address
    - owner-email                    # para BCC opcional al owner en eventos sensibles
  sends-email: true
env:
  default:
    LOG_LEVEL: INFO
    AWS_SES_REGION: us-east-1
    POWERTOOLS_SERVICE_NAME: auth-email-worker
    POWERTOOLS_METRICS_NAMESPACE: Portfolio/Auth
  prod:
    LOG_LEVEL: WARNING
```

El worker:
1. Recibe el mensaje.
2. Resuelve la plantilla por `kind` (5 plantillas en `core/templates/`).
3. Llama `send_email(...)`.
4. Inserta `auth_audit_log` event=`email.sent.<kind>` (success=true).
5. Si falla SES por motivo no-retryable (email rebotado dominio
   invalido), inserta `email.send.failed` y RETURN normal (no
   reintenta).
6. Si falla por motivo retryable (throttling), levanta excepcion ->
   SQS reintenta. Tras `max_receive_count=3` -> DLQ.

## 6. Lambda `auth` (manifest)

`serverless/lambda/services/auth/manifest.yaml`:

```yaml
name: auth
trigger:
  type: http
  method: POST
  path: /auth
runtime: python3.13
handler: core.handler.lambda_handler
memory: 384
timeout: 15
snap_start: true
uses:
  queues:
    - name: portfolio-auth-email-${stage}
      access: producer
  tables:
    cache: read-write                # @cached SSM cache
    rate-limit-rules: read-write
    rate-limit-buckets: read-write
    jwt-blacklist: read-write        # nueva
    auth-codes: read-write           # nueva
  secrets:
    - turnstile-secret
    - turnstile-bypass-secret
    - neon-url
    - jwt-secret                     # nueva
    - ses-from-address               # publica mensajes con este from
  sends-email: false                 # publica a SQS, NO envia directo
env:
  default:
    LOG_LEVEL: INFO
    POWERTOOLS_SERVICE_NAME: auth
    POWERTOOLS_METRICS_NAMESPACE: Portfolio/Auth
    JWT_ISSUER: portfolio-auth
    JWT_AUDIENCE: portfolio
    MAGIC_LINK_BASE_URL: https://api.portfolio.dev.the-full-stack.com/auth
  dev:
    CORS_ALLOWED_ORIGINS: 'https://portfolio.dev.the-full-stack.com,https://hub.portfolio.dev.the-full-stack.com,https://fintech.portfolio.dev.the-full-stack.com,https://architect.portfolio.dev.the-full-stack.com,https://leader.portfolio.dev.the-full-stack.com,https://vibe.portfolio.dev.the-full-stack.com,http://localhost:9970'
    MAGIC_LINK_BASE_URL: https://api.portfolio.dev.the-full-stack.com/auth
  stage:
    CORS_ALLOWED_ORIGINS: 'https://portfolio.stage.the-full-stack.com,https://hub.portfolio.stage.the-full-stack.com,https://fintech.portfolio.stage.the-full-stack.com,https://architect.portfolio.stage.the-full-stack.com,https://leader.portfolio.stage.the-full-stack.com,https://vibe.portfolio.stage.the-full-stack.com'
    MAGIC_LINK_BASE_URL: https://api.portfolio.stage.the-full-stack.com/auth
  prod:
    LOG_LEVEL: WARNING
    CORS_ALLOWED_ORIGINS: 'https://the-full-stack.com,https://www.the-full-stack.com,https://portfolio.the-full-stack.com,https://hub.portfolio.the-full-stack.com,https://fintech.portfolio.the-full-stack.com,https://architect.portfolio.the-full-stack.com,https://leader.portfolio.the-full-stack.com,https://vibe.portfolio.the-full-stack.com'
    MAGIC_LINK_BASE_URL: https://api.portfolio.the-full-stack.com/auth
```

## 7. IAM scopes esperados (los genera el provisioner desde el manifest)

`auth` IAM role:
- `dynamodb:GetItem`, `PutItem`, `Query` sobre las 5 tablas declaradas en `uses.tables`.
- `sqs:SendMessage` sobre `portfolio-auth-email-${stage}`.
- `ssm:GetParameter` sobre los 5 paths declarados en `uses.secrets`.
- `kms:Decrypt` sobre `alias/portfolio-lambdas` (necesario para los 2
  SecureString: `turnstile-secret`, `jwt-secret`).

`auth_email_worker` IAM role:
- `sqs:ReceiveMessage`, `DeleteMessage`, `GetQueueAttributes` sobre
  `portfolio-auth-email-${stage}`.
- `ssm:GetParameter` sobre `ses-from-address`, `owner-email`.
- `ses:SendEmail`, `SendRawEmail` sobre la identidad
  `no-reply@the-full-stack.com` (scoped por condition Resource).

## 8. Rate-limit rules (seed)

Insertar 5 reglas en la tabla `portfolio-rate-limit-rules-${stage}`
via el subcomando `serverless rate-limit set` (existente). Hacer 1 vez
por stage:

```bash
# register.start: 3 req/h/IP, blacklist 24h si excede 10/h
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/auth#register.start' --limit=3 --window=3600 \
  --hard-cap=10 --hard-cap-action=blacklist-24h --aws-profile=tfs-dev

# login.start: 5/min/IP
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/auth#login.start' --limit=5 --window=60 \
  --hard-cap=20 --hard-cap-action=blacklist-1h --aws-profile=tfs-dev

# verify.*: 10/min/IP (incluye verify-magic-link, verify-code,
#   set-password, resend-code)
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/auth#verify' --limit=10 --window=60 --aws-profile=tfs-dev

# session.refresh: 30/min/IP
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/auth#session.refresh' --limit=30 --window=60 --aws-profile=tfs-dev

# session.logout: 30/min/IP
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/auth#session.logout' --limit=30 --window=60 --aws-profile=tfs-dev
```

Repetir para `stage` y `prod`. Idempotente (overwrite).

## 9. Como se aplica todo

Orden de provisioning:

1. `serverless deploy --lambda=db --stage=dev` (asegura migration runner up).
2. `serverless run --stage=dev --lambda=db --event=events/migrate.json`
   (aplica `00000002_auth_schema.py`).
3. `serverless provision-infra --stage=dev` (crea las 2 DynamoDB nuevas + las 2 SQS nuevas + el SSM jwt-secret).
4. `serverless sync-secrets --stage=dev` (publica el JWT_SECRET a SSM).
5. `serverless deploy --lambda=auth_email_worker --stage=dev`.
6. `serverless deploy --lambda=auth --stage=dev`.
7. Seed de rate-limit rules (paso 8 arriba).

Mismo orden en `stage` y `prod`. El CI auto-detecta los cambios via
`change_detector.py` y arma el matrix correcto.
