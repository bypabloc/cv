---
name: auth-system
description: >
  Auth domain reference for the portfolio backend serverless: the Lambda
  `auth` (HTTP POST `/auth` with operations register / login / verify /
  session for refresh+logout), the Lambda `auth_email_worker` (SQS
  consumer + SES sender for magic-link and 8-char email codes), the
  shared subpackage `shared.auth` (pyjwt + argon2-cffi + Crockford-like
  code generator), the Neon schema with 5 tables auth_users /
  auth_credentials / auth_email_codes / auth_magic_links /
  auth_audit_log, the DynamoDB table portfolio-jwt-blacklist-${stage}
  with GSI by_family_id for token reuse detection, the SSM
  /portfolio/${stage}/jwt-secret SecureString with KMS encryption, the
  SQS portfolio-auth-email-${stage} + DLQ for email async, the JWT
  HS256 lifecycle (temp 5min rolling, access 15min stateless, refresh
  30days with family rotation), the rate-limit seeds for the 10
  endpoints (register.start, login.start, register.verify-magic-link,
  register.verify-code, login.verify-magic-link, login.verify-code,
  verify.set-password, verify.resend-code, session.refresh,
  session.logout), Turnstile mandatory in register.start and
  login.start, anti-enumeration UX (404 EMAIL_NOT_FOUND with
  suggest_register flag), magic-link as opaque 32-byte b64url token
  (NOT JWT) with SHA-256 hash in Neon and single-use semantics,
  argon2id default parameters from argon2-cffi PasswordHasher, the
  rolling temp JWT pattern between flow steps with blacklist
  rotation, the 302 redirect from magic-link GET to the dashboard
  callback with tokens in fragment hash (NOT query string), and the
  3-plan series ordering (01-auth-infra-basics is current scope,
  02-auth-mfa adds TOTP+WebAuthn, 03-auth-users-management adds the
  Lambda users with profile/admin).
  ALWAYS invoke this skill BEFORE answering ANY question about
  authentication, JWT, login, register, password, magic link, email
  code, MFA, OTP, session, refresh token, logout, user lockout,
  rate-limit on auth endpoints, the auth_users table, the
  jwt-blacklist DynamoDB table, the auth-email SQS queue, the
  jwt-secret SSM parameter, the shared.auth subpackage, the
  auth_email_worker Lambda, or the auth Lambda. NEVER answer auth
  questions from training data alone — this portfolio has consolidated
  decisions (split lambdas auth+users, hybrid Neon+DDB persistence,
  HS256 with rolling temp, Crockford-like 8-char codes, anti-
  enumeration 404, family_id reuse detection with GSI Query +
  BatchWriteItem, magic-link as opaque token NOT JWT, email async via
  dedicated SQS+worker NOT reusing contact_worker) that override
  generic advice.
  Use when the user says "auth", "autenticacion", "authentication",
  "login", "logout", "register", "registro", "signup", "signin",
  "magic link", "magic-link", "email code", "codigo por email",
  "verificacion email", "email verification", "password", "contrasena",
  "set password", "set-password", "reset password", "MFA", "TOTP",
  "WebAuthn", "passkeys", "JWT", "access token", "refresh token",
  "token refresh", "blacklist JWT", "jwt-blacklist", "token reuse",
  "session refresh", "session logout", "argon2", "argon2id",
  "auth_users", "auth_credentials", "auth_email_codes",
  "auth_magic_links", "auth_audit_log", "shared.auth", "auth_email_worker",
  "lambda auth", "auth lambda", "POST /auth", "/auth endpoint",
  "Turnstile auth", "anti enumeration", "user lockout", "account
  locked", "EMAIL_NOT_FOUND", "EMAIL_ALREADY_REGISTERED",
  "TOKEN_BLACKLISTED", "TOKEN_REUSE_DETECTED", "rate limit register",
  "rate limit login", "family_id", "by_family_id GSI", "rolling temp
  jwt", "jwt-secret SSM", "secret JWT", "HS256", "RS256",
  "JWT lifecycle", "JWT lifetime", "JWT claims", "JWT typ",
  "auth schema neon", "schema auth", "auth flow", "register flow",
  "login flow", "verify flow", "session flow", "callback dashboard
  auth", "fragment hash tokens", "302 magic link", "8 char code",
  "Crockford code", "code generator", "code hash", "compare_code",
  "verify_password", "hash_password", "issue_temp_jwt",
  "issue_access_jwt", "issue_refresh_jwt", "verify_jwt", "auth
  audit log", "audit auth", "auth security", "auth-system",
  "/auth-system", "plan auth-infra-basics", "auth plan 01",
  "auth plan 02", "auth plan 03", "auth-mfa", "auth-users-management",
  "users lambda", "lambda users", "perfil de usuario", "user profile",
  "auth deploy", "rotar jwt secret", "rotate jwt secret", "rotate
  JWT_SECRET", "como funciona el auth del portfolio", "mfa", "totp",
  "passkey", "passkeys", "webauthn", "2fa", "two factor",
  "autenticacion en dos pasos", "factor doble", "recovery codes",
  "codigos de recuperacion", "clone detection", "sign_count",
  "kms totp", "cifrar totp secret",
  "gestion de usuarios", "user management", "profile get", "profile update",
  "actualizar perfil", "cambiar email", "change email", "change-email",
  "confirmar cambio de email", "eliminar cuenta", "delete account",
  "delete-account", "borrar cuenta", "soft delete usuario", "soft-delete",
  "marketing consent", "gdpr consent", "consent log", "status del usuario",
  "user status", "sesiones activas", "active sessions", "list sessions",
  "revoke session", "cerrar sesion remota", "multi-device", "panel admin",
  "admin panel", "admin scope", "deshabilitar usuario", "disable user",
  "habilitar usuario", "enable user", "force logout", "forzar logout",
  "list users", "listar usuarios", "admin delete user", "hard delete user",
  "admin actions audit", "admin whitelist", "admin-emails", "whitelist admin",
  "require_admin", "is_admin", "auth_user_sessions", "auth_user_admin_actions",
  "auth_user_consent_log", "POST /users", "/users endpoint", "lambda users plan 03",
  "session tracking", "family_id en access", "current session".
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Glob, Grep
---

# Auth system reference

> Knowledge tree del dominio de autenticacion del backend del portfolio.
> Detalle completo en [.claude/docs/auth-system/](../../docs/auth-system/)
> + rule [.claude/rules/auth-system.md](../../rules/auth-system.md).

## Componentes (snapshot)

| Componente | Donde vive |
|---|---|
| Lambda `auth` (HTTP) | `serverless/lambda/services/auth/` |
| Lambda `auth_email_worker` (SQS) | `serverless/lambda/services/auth_email_worker/` |
| `shared.auth` (pyjwt + argon2 + codes) | `serverless/lambda/shared/auth/` |
| Schema Neon `auth_*` (5 tablas) | `serverless/lambda/shared/db/models/auth/` |
| Migration 00000002 | `serverless/lambda/shared/db/alembic/versions/00000002_auth_schema.py` |
| DDB `jwt-blacklist` + GSI `by_family_id` | `serverless/lambda/resources/dynamodb/jwt-blacklist.yaml` |
| SQS `auth-email-queue` + DLQ | `serverless/lambda/resources/sqs/auth-email-*.yaml` |
| SSM `jwt-secret` (SecureString + KMS) | `serverless/lambda/resources/secrets/jwt-secret.yaml` |

## Operations (Lambda `auth`)

| operation | actions |
|---|---|
| `register` | `start`, `verify-magic-link`, `verify-code` |
| `login` | `start`, `verify-magic-link`, `verify-code` |
| `verify` | `set-password`, `resend-code` |
| `session` | `refresh`, `logout` |

## Decisiones cerradas (NO reabrir)

1. **Split `auth` + futuro `users`**.
2. **Persistencia hibrida**: Neon (relacional + codes + magic links) +
   DDB (`jwt-blacklist` con TTL=exp + GSI `by_family_id`).
3. **JWT HS256** con SSM secret. 3 tipos: `temp` (5 min rolling),
   `access` (15 min stateless), `refresh` (30 dias, rotation +
   `family_id`).
4. **Codigo 8 chars Crockford-like** (alfabeto sin O/0/I/1/L). TTL 15
   min. Max 5 attempts.
5. **Magic link opaco** (NO JWT): 32 bytes b64url, hash SHA-256 en
   Neon. Single-use, TTL 15 min.
6. **Email async** via SQS dedicada + worker dedicado (NO reusa
   `contact_worker`).
7. **Turnstile solo en `register.start` y `login.start`**. El resto
   confia en JWT temp + rate-limit.
8. **Login UX anti-enumeration**: 404 EMAIL_NOT_FOUND con
   `suggest_register` que diferencia "no existe" (true) vs
   "disabled/locked" (false).
9. **FK `auth_users.profile_id`** NULLABLE a `cv_profiles.id`,
   ON DELETE SET NULL.
10. **argon2id** con defaults de `PasswordHasher()`.
11. **Rate-limit** reusa `shared.rate_limit` con seeds via
    `serverless rate-limit set`.
12. **CI** auto-detecta los Lambdas nuevos via `change_detector.py`.

## JWT lifecycle (resumen)

- `temp` (5 min): rolling. Cada paso del flujo blacklistea el `jti`
  recibido y emite uno nuevo (`step+1`).
- `access` (15 min): stateless. Lookup `jti` en DDB blacklist.
- `refresh` (30 dias): rotation + `family_id` (uuidv7 por login). Si
  llega un refresh ya blacklisted -> Query GSI by_family_id -> revoca
  TODA la familia -> 401 TOKEN_REUSE_DETECTED.

Claims: `sub` (user_id), `jti`, `typ`, `iat`, `exp`, `iss`, `aud`,
`flow`/`step` (solo temp), `family_id` (solo refresh). **El email NUNCA
viaja en el JWT**.

## Rate-limit (snapshot)

Detalle en
[.claude/docs/auth-system/03-rate-limit-rules.md](../../docs/auth-system/03-rate-limit-rules.md).

| Endpoint | Limit | Window |
|---|---|---|
| `register.start` | 3 | 3600s |
| `login.start` | 5 | 60s |
| `register.verify-*` / `login.verify-*` | 10 | 60s |
| `verify.set-password` | 5 | 60s |
| `verify.resend-code` | 3 | 300s |
| `session.refresh` / `session.logout` | 30 | 60s |

## Cuando NO usar esta skill

- Preguntas sobre el admin Next.js (`admin.portfolio.*`) que NO
  toquen el contrato del Lambda `auth`. Usar skill `admin-stack`.
- Preguntas sobre el form de contacto (`contact_form` + `contact_worker`).
- Preguntas generales sobre Lambda Python (manifest, deploy, testing)
  que NO involucren auth. Usar skill `lambda-controller`.
- Preguntas sobre Neon en general (operacion, migrations, branches).
  Usar skill `neon` y rule `neon-management`.

## Referencias cruzadas

- [.claude/docs/auth-system/](../../docs/auth-system/) — knowledge tree
- [.claude/rules/auth-system.md](../../rules/auth-system.md) — rule
- [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md)
- [.claude/rules/lambda-shared-imports.md](../../rules/lambda-shared-imports.md)
- [.claude/rules/neon-management.md](../../rules/neon-management.md)
- [.claude/rules/serverless-secrets.md](../../rules/serverless-secrets.md)
