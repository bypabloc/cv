# Sistema de autenticacion del portfolio

> Knowledge tree del dominio auth del backend serverless. Sobrevive al
> merge del plan `docs/specs/01-auth-infra-basics/` (efimero). Fuente de
> verdad para decisiones de arquitectura, JWT lifecycle, schema Neon,
> flujos, rate-limit y operacion.

## Componentes

| Componente | Que es | Donde vive |
|---|---|---|
| Lambda `auth` | HTTP POST `/auth` — register, login, verify, session (refresh/logout) | `serverless/lambda/services/auth/` |
| Lambda `auth_email_worker` | SQS consumer — renderiza y envia magic-link + code por SES | `serverless/lambda/services/auth_email_worker/` |
| `shared.auth` | Portador unico de `pyjwt` + `argon2-cffi` + generador de codes/tokens | `serverless/lambda/shared/auth/` |
| Schema Neon `auth_*` | 5 tablas: users, credentials, email_codes, magic_links, audit_log | `serverless/lambda/shared/db/models/auth/` |
| DynamoDB `jwt-blacklist` | Blacklist de JWTs (temp/access/refresh) con TTL=exp + GSI `by_family_id` | `serverless/lambda/resources/dynamodb/jwt-blacklist.yaml` |
| SQS `auth-email-queue` + DLQ | Cola de emails async | `serverless/lambda/resources/sqs/auth-email-{queue,dlq}.yaml` |
| SSM `/portfolio/${stage}/jwt-secret` | HS256 secret para JWT signing | `serverless/lambda/resources/secrets/jwt-secret.yaml` |

## Cuando leer

| Tema | Archivo |
|------|---------|
| JWT lifecycle (temp/access/refresh, rotation, blacklist, family detection) | [01-jwt-lifecycle.md](01-jwt-lifecycle.md) |
| Flujos (diagrama ASCII de cada operacion) | [02-flows.md](02-flows.md) |
| Reglas de rate-limit activas | [03-rate-limit-rules.md](03-rate-limit-rules.md) |

## Decisiones clave (cerradas)

1. **Split de lambdas**: `auth` (signup/signin/session) + futuro `users`
   (profile/admin). Este dominio entrega `auth` solamente.
2. **Persistencia hibrida**: estado relacional + codes + magic links en
   Neon (`auth_*`), blacklist de JWTs en DynamoDB (lookup O(1) por `jti`
   en cada request autenticada).
3. **JWT HS256** firmado con secret de SSM. 3 tipos:
   - `typ=temp` (5 min, rolling refresh entre pasos del flujo).
   - `typ=access` (15 min, stateless con verificacion blacklist).
   - `typ=refresh` (30 dias, rotacion + `family_id` para detectar reuso).
4. **Codigo de 8 chars Crockford-like**: alfabeto `A-Z + 0-9` sin
   `O/0/I/1/L` (30 chars, espacio = 30^8 ~ 6.5x10^11). Max 5 intentos
   por code, TTL 15 min.
5. **Magic link**: token opaco 32 bytes b64url (NO JWT). Hash SHA-256
   guardado en Neon. Single-use, TTL 15 min.
6. **Email async**: cola SQS `portfolio-auth-email-${stage}` + worker
   `auth_email_worker` (NO se reusa `contact_worker` — aislamiento de
   dominios).
7. **Turnstile**: obligatorio en `register.start` y `login.start`. El
   resto del flujo confia en el JWT temp + rate-limit.
8. **Login UX (email no existe)**: 404 +
   `{suggest_register: true, methods: []}`. Si existe + active sin
   password: 200 + `{methods: ['magic-link', 'email-code']}`.
9. **FK profile_id**: `auth_users.profile_id` -> `cv_profiles.id`
   NULLABLE (ON DELETE SET NULL). Solo el row de Pablo apuntara.
10. **Hash de password**: argon2id (defaults de argon2-cffi
    `PasswordHasher()`: time_cost=3, memory_cost=64MiB, parallelism=4).
11. **Rate-limit**: reusa `shared.rate_limit.check_or_raise` con reglas
    nuevas seedeadas via `serverless rate-limit set`.
12. **CI**: `change_detector.py` auto-detecta cambios en
    `services/auth/` y `services/auth_email_worker/` — cero cambio en
    `deploy-backend.yml`.

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** los services importan paquetes externos via
  `shared.<subpaquete>` (lambda-shared-imports).
- **SIEMPRE** un controller por action; logica de negocio en
  `core/services/`, NUNCA en controllers ni handler.
- **SIEMPRE** `auth_users.email` se guarda lowercased
  (`email.lower().strip()`).
- **SIEMPRE** los logs NO incluyen email completo (solo hash truncado),
  password, JWT, magic-link token, code. Auditoria en `auth_audit_log`.
- **SIEMPRE** el JWT_SECRET se lee de SSM en cold start (cached con
  `@cached_property` en AppConfig). NUNCA env var directa.
- **NUNCA** devolver `404` con body distinto entre "email no existe" y
  "email existe pero esta `disabled`/`locked`" — anti enumeration.
- **NUNCA** loguear el valor de `JWT_SECRET`, Neon URL, code o magic
  link token.
- **NUNCA** firmar un JWT con un secret distinto del leido de SSM.

## Operacion

```bash
# Aplicar migration nueva
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/migrate.json --aws-profile=tfs-dev

# Provision recursos compartidos (DDB jwt-blacklist + SQS + SSM jwt-secret)
python devtools/run.py serverless provision-infra --stage=dev \
  --aws-profile=tfs-dev

# Sync JWT_SECRET (categoria server)
python devtools/run.py serverless sync-secrets --stage=dev \
  --aws-profile=tfs-dev

# Deploy lambdas
python devtools/run.py serverless deploy --lambda=auth_email_worker \
  --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=auth \
  --stage=dev --aws-profile=tfs-dev

# Seed de rate-limit (1 vez por stage)
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='register.start' --limit=3 --window=3600 \
  --aws-profile=tfs-dev
# ... otras reglas en 03-rate-limit-rules.md
```

## Referencias cruzadas

- [.claude/rules/auth-system.md](../../rules/auth-system.md) — rule de
  enforcement
- [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md)
  — patron general de Lambdas
- [.claude/rules/lambda-shared-imports.md](../../rules/lambda-shared-imports.md)
  — catalogo de portadores
- [.claude/rules/neon-management.md](../../rules/neon-management.md) —
  operacion de Neon (DB_URL en SSM, migrations via la Lambda `db`)
- [.claude/rules/serverless-secrets.md](../../rules/serverless-secrets.md)
  — inventario SSM (incluye `jwt-secret`)
- [.claude/docs/serverless-backend/README.md](../serverless-backend/README.md)
  — arquitectura general del backend
- [docs/diagrams/db-er.mmd](../../../docs/diagrams/db-er.mmd) — schema
  Neon (incluye cluster `auth_*`)
- Skill: `/auth-system`
