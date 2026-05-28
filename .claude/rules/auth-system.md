# Sistema de autenticacion del portfolio

> Reglas duras para trabajar con los Lambdas `auth` + `auth_email_worker`,
> el subpackage `shared.auth`, el schema `auth_*` en Neon, la tabla DDB
> `jwt-blacklist` y los flujos register/login/verify/session. Aplica al
> backend serverless. NO aplica al frontend Astro ni al dashboard Next.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Cualquier archivo bajo `serverless/lambda/services/auth/`
- Cualquier archivo bajo `serverless/lambda/services/auth_email_worker/`
- Cualquier archivo bajo `serverless/lambda/shared/auth/`
- Cualquier archivo bajo `serverless/lambda/shared/db/models/auth/`
- `serverless/lambda/shared/db/repositories/auth.py`
- `serverless/lambda/shared/db/alembic/versions/*auth*`
- `serverless/lambda/resources/dynamodb/jwt-blacklist.yaml`
- `serverless/lambda/resources/sqs/auth-email-{queue,dlq}.yaml`
- `serverless/lambda/resources/secrets/jwt-secret.yaml`
- Cualquier referencia a `/portfolio/${stage}/jwt-secret` en SSM
- Decisiones sobre JWT (HS256, lifetimes, claims, family_id, rotation)
- Decisiones sobre rate-limit de los endpoints `/auth?operation=...`

## Reglas duras (SIEMPRE / NUNCA)

### Estructura y patrones

- **SIEMPRE** los services del Lambda `auth` siguen `lambda-controller`:
  controller orquesta + service tiene la logica + Pydantic models
  validan el payload. Logica de negocio NUNCA en handler ni controllers.
- **SIEMPRE** un controller por action. Archivo en
  `controllers/<operation>/<action_snake>.py` y clase `<ActionPascal>`.
- **SIEMPRE** el handler delgado: `lambda_handler` -> `http_handler(
  event, event_model=EVENT_MODEL, cors_origin='echo',
  success_status=200, metric_names={...})`. Sin negocio.
- **SIEMPRE** todos los paquetes externos (`pyjwt`, `argon2-cffi`) se
  importan via `shared.auth` (NUNCA `import jwt` ni `import argon2` en
  `core/`). Mismo patron para boto3 / sqlalchemy / aws-lambda-powertools.
- **SIEMPRE** los services importan SQLAlchemy via `shared.db` y boto3
  via `shared.aws`.

### Secretos y datos sensibles

- **SIEMPRE** el JWT_SECRET se lee de SSM en cold start usando
  `AppConfig.jwt_secret` (`@cached_property` que llama
  `get_secret_by_name('jwt-secret', local_env='JWT_SECRET')`).
- **SIEMPRE** el `auth_users.email` se guarda lowercased
  (`email.lower().strip()`).
- **SIEMPRE** los codes se guardan como `bytea` (SHA-256 hash) en
  `auth_email_codes.code_hash`. NUNCA en plain text.
- **SIEMPRE** los magic-link tokens se guardan como `bytea` (SHA-256
  hash) en `auth_magic_links.token_hash`. NUNCA en plain text.
- **SIEMPRE** las passwords se hashean con argon2id via
  `shared.auth.hash_password()`. NUNCA bcrypt ni SHA-256 ni plain text.
- **NUNCA** loguear: JWT, magic-link token, code, password, email
  completo, Neon URL, JWT_SECRET. El audit log va a `auth_audit_log`
  (Neon), no a CloudWatch logs.
- **NUNCA** firmar un JWT con un secret distinto del leido de SSM.

### JWT lifecycle

- **SIEMPRE** HS256.
- **SIEMPRE** 3 tipos validos: `temp` (5 min, rolling), `access` (15
  min), `refresh` (30 dias, rotation + `family_id`).
- **SIEMPRE** cada API del flujo verifica el `temp_token` recibido,
  blacklistea su `jti` y emite uno nuevo (rolling).
- **SIEMPRE** cada login emite un `family_id` (uuidv7) nuevo. Cada uso
  de refresh rota dentro de la misma familia.
- **SIEMPRE** si llega un refresh con `jti` ya blacklisted (reuso
  detectado): revocar TODA la familia via Query GSI `by_family_id` +
  BatchWriteItem (max 25 por call, paginar). Devolver `401
  TOKEN_REUSE_DETECTED` + audit `session.refresh.reuse_detected`.
- **NUNCA** poner email u otros datos de perfil en los claims del JWT.
  El JWT contiene SOLO `sub` (user_id) como identificador.
- **NUNCA** reusar el mismo `family_id` entre logout y nuevo login.
  Cada login = nuevo `family_id`.

### Schema Neon

- **SIEMPRE** las 5 tablas `auth_*` se crean con la migration
  `00000002_auth_schema.py` (Alembic). Cambios futuros: migration nueva,
  NUNCA editar la 00000002 aplicada.
- **SIEMPRE** los enums `auth_user_status`, `auth_code_kind`,
  `auth_link_kind` se crean con `op.execute('CREATE TYPE ...')` o
  `postgresql.ENUM(...).create(op.get_bind())`. NUNCA `String` con
  CHECK constraint.
- **SIEMPRE** `auth_users.profile_id` es FK NULLABLE a `cv_profiles.id`
  con ON DELETE SET NULL.
- **SIEMPRE** `auth_users.email` es `CITEXT` UNIQUE.
- **NUNCA** borrar las tablas `auth_*` en `prod` con `downgrade`.
  Cualquier rollback se hace con migration forward que revierta.

### Login UX (anti enumeration)

- **SIEMPRE** `login.start` con email inexistente devuelve `404
  {error: 'EMAIL_NOT_FOUND', suggest_register: true}`.
- **SIEMPRE** `login.start` con email cuyo status es `disabled` o
  `locked` devuelve EL MISMO `404 {error: 'EMAIL_NOT_FOUND',
  suggest_register: false}` (anti-enumeration). Audit log registra el
  intento con `error_code='ACCOUNT_DISABLED'` o `'ACCOUNT_LOCKED'`.
- **SIEMPRE** `login.start` con email cuyo status es `pending` devuelve
  `409 PENDING_VERIFICATION` para forzar que termine el flujo de register.
- **NUNCA** devolver 404 con body distinto entre "no existe" y
  "existe + disabled/locked". La diferencia visible al cliente es solo
  `suggest_register`.

### Turnstile y rate-limit

- **SIEMPRE** Turnstile obligatorio en `register.start` y `login.start`
  (AC-12). El resto del flujo NO valida Turnstile — confia en el JWT
  temp + rate-limit.
- **SIEMPRE** rate-limit per-IP via `shared.rate_limit.check_or_raise`
  con las reglas seedeadas (ver
  [.claude/docs/auth-system/03-rate-limit-rules.md](../docs/auth-system/03-rate-limit-rules.md)).
- **SIEMPRE** la verificacion de Turnstile + rate-limit ocurre ANTES
  de tocar Neon o SQS.

### Email async (SQS + worker)

- **SIEMPRE** el Lambda `auth` solo publica a la cola SQS
  `portfolio-auth-email-${stage}`. NUNCA llama SES directo.
- **SIEMPRE** el `auth_email_worker` consume la cola con
  `ReportBatchItemFailures` (permite fallar un mensaje del batch y
  reintentarlo sin afectar al resto).
- **SIEMPRE** el worker tras enviar exitosamente inserta un row en
  `auth_audit_log` con `event=email.sent.<kind>` (success=true).
- **NUNCA** reusar `contact_worker` para emails de auth — aislamiento
  de dominios.

### IAM y costos

- **SIEMPRE** el Lambda `auth` tiene IAM scoped: las 5 tablas DDB
  declaradas en `manifest.yaml#uses.tables`, la cola SQS, los 5 secretos
  SSM. NUNCA wildcard.
- **SIEMPRE** el `auth_email_worker` tiene IAM scoped: SQS por ARN
  exacto, SSM `ses-from-address` por ARN exacto, SES por **identity ARN
  exacto** (`arn:aws:ses:us-east-1:<account-id>:identity/the-full-stack.com`).
  NUNCA `Resource: *` ni `ses:*`.

### Anti-patrones (correcciones criticas)

| Anti-patron | Correccion |
|---|---|
| `import jwt` en el `core/` de auth | `from shared.auth import issue_temp_jwt, verify_jwt, ...` |
| `import argon2` o `from passlib import ...` | `from shared.auth import hash_password, verify_password` |
| Comparar codes con `==` (timing attack) | `from shared.auth import compare_code` (secrets.compare_digest) |
| Generar code con `random.choice` | `secrets.choice` via `shared.auth.generate_code` (CSPRNG) |
| Loggear JWT/code/token | log solo `jti`, `user_id`, `event`, NUNCA el valor |
| Email distinto en respuesta a "no existe" vs "disabled" | Mismo 404, solo `suggest_register` cambia |
| Token de magic-link como JWT | Opaco 32 bytes b64url; hash SHA-256 en `auth_magic_links.token_hash` |
| Hardcodear secret en `manifest.yaml` | SSM SecureString + KMS; `@cached_property` en AppConfig |
| Lambda `auth` enviando SES directo | Publicar a SQS; el worker es quien envia |
| Reusar `family_id` entre sesiones | Cada login = `family_id` nuevo (uuidv7) |
| Editar migration `00000002` ya aplicada | Migration nueva (forward fix) |
| Rate-limit con prefix matching | Exacto `<operation>.<action>` literal |

## Verificacion antes de commit (recordatorio)

```bash
# Tests del subpackage shared.auth
python devtools/run.py serverless tests --type=unit --shared

# Tests del Lambda auth
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth   # >=80% per-file

# Lint deps (shared-only imports + dedup D-3)
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless lint-deps --lambda=auth_email_worker
python devtools/run.py serverless lint-deps --shared
```

## Referencias cruzadas

- [.claude/docs/auth-system/README.md](../docs/auth-system/README.md) —
  knowledge tree del dominio
- [.claude/docs/auth-system/01-jwt-lifecycle.md](../docs/auth-system/01-jwt-lifecycle.md)
- [.claude/docs/auth-system/02-flows.md](../docs/auth-system/02-flows.md)
- [.claude/docs/auth-system/03-rate-limit-rules.md](../docs/auth-system/03-rate-limit-rules.md)
- [.claude/rules/lambda-controller.md](lambda-controller.md) — patron
  general
- [.claude/rules/lambda-shared-imports.md](lambda-shared-imports.md) —
  catalogo de portadores
- [.claude/rules/neon-management.md](neon-management.md) — operacion de
  Neon (migrations via la Lambda `db`, branches)
- [.claude/rules/serverless-secrets.md](serverless-secrets.md) — SSM +
  KMS + IAM scopes
- Skill: `/auth-system`
