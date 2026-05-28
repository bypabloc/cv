# Plan 01: Auth infra basics — Lambda `auth` con register / login / verify / logout

> **Orden en la serie auth**: este es el **1 de 3** planes secuenciales.
>
> ```text
> 01 — auth-infra-basics       <-- ESTE PLAN (infra + register/login/verify/logout)
> 02 — auth-mfa                (TOTP + email-code MFA + WebAuthn / Passkeys)
> 03 — auth-users-management   (Lambda `users` con profile/status/admin)
> ```
>
> Los planes son secuenciales: el plan 02 depende del 01 (shared.auth, schema
> Neon, lambda auth con flujo basico), y el plan 03 del 01+02 (status del
> usuario, login con MFA validado). NO se ejecutan en paralelo entre si.
>
> Entrega el esqueleto del dominio de autenticacion del portfolio: schema Neon
> `auth_*`, nuevo shared subpackage `shared.auth` (JWT HS256 + argon2 +
> generador de codigos), 1 tabla DynamoDB nueva (`jwt-blacklist` con GSI
> `by_family_id`), cola SQS `auth-email-queue` + Lambda worker
> `auth_email_worker`, y Lambda HTTP `auth` con SOLO los flujos basicos (sin
> MFA, sin WebAuthn, sin CRUD de users): `register`, `login`, `verify`
> (magic-link + email-code), `logout`, `refresh-token`.

## Que entrega este plan

- Schema Neon: tablas `auth_users`, `auth_credentials`, `auth_email_codes`,
  `auth_magic_links`, `auth_audit_log` (Alembic migration `00000002`).
- Shared subpackage `shared.auth`: portador unico de `pyjwt` y
  `argon2-cffi`; funciones `issue_temp_jwt`, `issue_access_jwt`,
  `issue_refresh_jwt`, `verify_jwt`, `hash_password`, `verify_password`,
  `generate_code` (8 chars Crockford-like sin O/0/I/1/L), `generate_token`.
- DynamoDB: tabla `portfolio-jwt-blacklist-${stage}` (TTL `exp`) con
  GSI `by_family_id` (KEYS_ONLY) para revocar familias de refresh
  tokens.
- SSM: parametro nuevo `/portfolio/${stage}/jwt-secret` (SecureString +
  KMS `alias/portfolio-lambdas`).
- SQS: cola `portfolio-auth-email-${stage}` + DLQ.
- Lambda `auth_email_worker`: consume la cola, envia via SES (template
  texto + HTML) magic link, register-code, login-code, otp-code,
  password-reset.
- Lambda `auth`: HTTP POST `/auth`. Operations + actions:
  - `register.start` (email -> envia magic-link + code, JWT temp)
  - `register.verify-magic-link` (token -> JWT final)
  - `register.verify-code` (code -> JWT final)
  - `login.start` (email -> 404 + suggest_register o lista de metodos)
  - `login.verify-magic-link` (token -> JWT final)
  - `login.verify-code` (code -> JWT final)
  - `verify.set-password` (JWT temp + password -> guarda hash)
  - `verify.resend-code` (JWT temp -> regenera + reenvia)
  - `session.refresh` (refresh JWT -> nuevo access + refresh rotado)
  - `session.logout` (access JWT -> blacklist + invalida refresh)
- Rate-limit estricto: `register.start` 3/h/IP, `login.start` 5/min/IP,
  `verify.*` 10/min/IP, `session.refresh` 30/min/IP.
- Turnstile obligatorio en `register.start` y `login.start`.
- 1 commit por fase, cada uno con verificacion incremental. PR a `dev`.

## Que NO entrega este plan (queda para plan 2 y 3)

- MFA (TOTP), email-code-como-MFA, WebAuthn / Passkeys → **plan 2**.
- Lambda `users` (profile, status, admin, deshabilitar usuario) → **plan 3**.
- Frontend Astro de signup / signin / verify / dashboard → plan futuro.

## Cuando leer

| Tema | Archivo |
|------|---------|
| Problema, solucion, AC numerados | [01-contexto-y-decision.md](01-contexto-y-decision.md) |
| Schema Neon `auth_*` + ER ASCII | [02-schema-neon.md](02-schema-neon.md) |
| Shared subpackage `shared.auth` (JWT, argon2, code gen) | [03-shared-auth.md](03-shared-auth.md) |
| Infraestructura: DynamoDB nuevas, SSM, SQS, cola + worker | [04-infraestructura.md](04-infraestructura.md) |
| Arquitectura del Lambda `auth`: operations, actions, controllers, services | [05-lambda-auth-arquitectura.md](05-lambda-auth-arquitectura.md) |
| Estrategia de testing (unit por capa + integration por endpoint) | [06-testing.md](06-testing.md) |
| Listado de archivos afectados con verificacion por archivo | [07-archivos-afectados.md](07-archivos-afectados.md) |
| Descomposicion en tareas atomicas paralelizables | [08-descomposicion-paralelizacion.md](08-descomposicion-paralelizacion.md) |
| Commits incrementales (Conventional Commits espanol) | [09-commits.md](09-commits.md) |
| Paralelizacion con git worktrees | [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) |
| Verificacion E2E iterativa (fase final, gate del PR) | [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Estado por fase

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Plan escrito + carpeta `docs/specs/auth-infra-basics/` commiteada | pending |
| 1 | Schema Neon `auth_*` + Alembic migration 00000002 | pending |
| 2 | `shared.auth` subpackage (pyjwt + argon2-cffi + code/token gen + tests) | pending |
| 3 | DynamoDB table (`jwt-blacklist` + GSI `by_family_id`) + SSM `jwt-secret` + SQS `auth-email-queue` | pending |
| 4 | Lambda `auth_email_worker` (consume cola, envia SES) | pending |
| 5 | Lambda `auth` scaffold (manifest + AppConfig + handler + EventModel + OPERATIONS) | pending |
| 6 | Operation `register` (start + verify-magic-link + verify-code) | pending |
| 7 | Operation `login` (start + verify-magic-link + verify-code) | pending |
| 8 | Operation `verify` (set-password + resend-code) | pending |
| 9 | Operation `session` (refresh + logout) | pending |
| 10 | Rate-limit rules + integracion `check_or_raise` por endpoint | pending |
| 11 | Verificacion E2E + limpieza de `docs/specs/auth-infra-basics/` | pending |

## Decisiones no-reabribles

Cerradas en el dialogo previo y NO se vuelven a discutir:

1. **Split de lambdas**: `auth` + `users`. Este plan entrega `auth`. `users` -> plan 3.
2. **Persistencia hibrida minima**: estado relacional + codes + magic
   links en Neon (`auth_*`), blacklist de JWTs en DynamoDB
   (`jwt-blacklist` con GSI `by_family_id`). Solo blacklist va a DDB
   porque cada request autenticada hace lookup O(1) por `jti`; codes y
   magic links se verifican una sola vez por flow, latencia Neon
   ~10-30ms es invisible. Decision documentada en el contexto.
3. **JWT**: HS256 + secret en SSM SecureString. Tres tipos:
   - **temp** (`typ=temp`): 5 min, rolling refresh (cada API del flujo
     emite uno nuevo y blacklistea el anterior).
   - **access** (`typ=access`): 15 min. Stateless. Blacklisteable.
   - **refresh** (`typ=refresh`): 30 dias. Stateful (row en
     `jwt-blacklist` con TTL = exp). Rotacion en cada uso.
4. **Codigo de 8 chars**: alfabeto Crockford-like (`A-Z` + `0-9` sin
   `O/0/I/1/L`). TTL 15 min. Max 5 intentos por code (`auth_email_codes.attempts`).
5. **Magic link**: token opaco 32 bytes b64url (URL-safe). TTL 15 min,
   single-use. URL: `https://api.portfolio.{env}.the-full-stack.com/auth?operation=register&action=verify-magic-link&token=<X>` (API directa, devuelve HTML 200 con redirect + auto-submit del JWT).
6. **Email async**: cola SQS dedicada `portfolio-auth-email-${stage}` +
   worker dedicado `auth_email_worker` (NO reusar `contact_worker` —
   aislamiento de dominios).
7. **Turnstile**: solo en `register.start` y `login.start`. El resto del
   flujo confia en el JWT temp + rate-limit.
8. **Login UX (email no existe)**: 404 + `{suggest_register: true,
   methods: []}`. Si existe: 200 + `{methods: [...]}` con la lista
   habilitada (en este plan solo `magic-link` y `email-code` ya que
   password/MFA llegan en fases posteriores y plan 2).
9. **Link cv_profiles**: `auth_users.profile_id` FK NULLABLE a
   `cv_profiles(id)` (ON DELETE SET NULL). Default `NULL`; solo el row
   de Pablo apuntara cuando se setee a mano.
10. **Hash de password**: argon2id (parametros defaults de argon2-cffi
    `PasswordHasher()`: `time_cost=3`, `memory_cost=65536`, `parallelism=4`).
11. **Rate-limit**: reusar `shared.rate_limit` con reglas nuevas por
    endpoint (insertadas en la tabla `portfolio-rate-limit-rules` via
    `serverless rate-limit` command, no codigo).
12. **CI**: `change_detector.py` auto-detecta los nuevos `services/auth/`,
    `services/auth_email_worker/` — cero cambio en `deploy-backend.yml`.

## Reglas criticas (siempre activas)

- **SIEMPRE** los services importan paquetes externos via
  `shared.<subpaquete>` (ver
  [.claude/rules/lambda-shared-imports.md](../../.claude/rules/lambda-shared-imports.md)).
- **SIEMPRE** un controller por action; nombre de clase
  `action.capitalize()` con palabra simple (ej. `Start`, `VerifyMagicLink` ->
  pero el verbo se separa con guion en el wire y la clase es la version
  capitalizada del segmento `<action>`: `verify-magic-link` -> `VerifyMagicLink`
  en `controllers/register/verify_magic_link.py`).
- **SIEMPRE** la logica de negocio vive en `core/services/`, NUNCA en el
  handler ni en los controllers.
- **SIEMPRE** `auth_users.email` se guarda lowercased (`email.lower().strip()`).
- **SIEMPRE** logs NO incluyen: email completo (solo hash truncado),
  password, JWT, magic-link token, code. Auditoria queda en
  `auth_audit_log`. Aplica la politica general de
  [.claude/rules/security.md](../../../.claude/rules/security.md)
  ("Credenciales y secretos").
- **SIEMPRE** verificar antes de commitear (lint + tests unit del scope).
- **NUNCA** devolver `404` con body distinto entre "email no existe" y
  "email existe pero esta deshabilitado". Solo `register.start` y
  `login.start` distinguen (y solo si Turnstile valido).
- **NUNCA** loguear el valor de `JWT_SECRET`, Neon URL, codigo de email
  o token de magic-link.
- **NUNCA** firmar un JWT con un secret distinto del leido de SSM en
  cold start (NO env var directa).

## Matriz de verificacion (rapida)

| Capa | Comando |
|------|---------|
| Sintaxis Python | `python -m compileall -q serverless/lambda/services/auth serverless/lambda/services/auth_email_worker serverless/lambda/shared/auth` |
| Imports shared-only | `python devtools/run.py serverless lint-deps --lambda=auth` |
| Tests unit `shared.auth` | `python devtools/run.py serverless tests --type=unit --shared` |
| Tests unit `auth` | `python devtools/run.py serverless tests --type=unit --lambda=auth` |
| Tests unit `auth_email_worker` | `python devtools/run.py serverless tests --type=unit --lambda=auth_email_worker` |
| Coverage | `python devtools/run.py serverless tests --type=coverage --lambda=auth` |
| Migration up (dev) | `python devtools/run.py serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev` |
| Run local (RIE) | `python devtools/run.py serverless run --stage=local --lambda=auth --event=events/register-start.json` |
| Deploy dev | `python devtools/run.py serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev` |
| Smoke E2E | ver [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Bibliografia interna

- [.claude/rules/lambda-controller.md](../../.claude/rules/lambda-controller.md) — formato Lambda Python
- [.claude/rules/lambda-shared-imports.md](../../.claude/rules/lambda-shared-imports.md) — catalogo de portadores
- [.claude/rules/neon-management.md](../../.claude/rules/neon-management.md) — Neon en runtime + migrations
- [.claude/rules/serverless-secrets.md](../../.claude/rules/serverless-secrets.md) — SSM + IAM scopes
- [.claude/rules/ci-cd-pipeline.md](../../.claude/rules/ci-cd-pipeline.md) — `deploy-backend.yml` auto-detect
- [.claude/docs/serverless-backend/README.md](../../.claude/docs/serverless-backend/README.md) — arquitectura general
- [.claude/docs/serverless-rate-limit/README.md](../../.claude/docs/serverless-rate-limit/README.md) — sliding window
- [.claude/docs/dynamodb-cache/README.md](../../.claude/docs/dynamodb-cache/README.md) — @cached
- [docs/diagrams/db-er.mmd](../../diagrams/db-er.mmd) — schema Neon actual
- [serverless/lambda/services/contact_form/](../../../serverless/lambda/services/contact_form/) — analogo (HTTP + Turnstile + SQS publish)
- [serverless/lambda/services/contact_worker/](../../../serverless/lambda/services/contact_worker/) — analogo (SQS consumer + SES send)
