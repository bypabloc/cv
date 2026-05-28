# Plan 02: Auth MFA — TOTP + email-code-as-MFA + WebAuthn / Passkeys

> **Orden en la serie auth**: este es el **2 de 3** planes secuenciales.
>
> ```text
> 01 — auth-infra-basics       (DEPENDENCIA: shared.auth + schema + lambda auth basico)
> 02 — auth-mfa                <-- ESTE PLAN (TOTP + email-MFA + WebAuthn)
> 03 — auth-users-management   (Lambda `users` con profile/status/admin)
> ```
>
> **Dependencia dura**: requiere el plan 01 completamente mergeado a `dev`
> (idealmente a `main`). Este plan extiende el Lambda `auth` con las
> operations `mfa` y `webauthn`, agrega 3 tablas Neon
> (`auth_mfa_methods`, `auth_webauthn_credentials`, `auth_webauthn_challenges`)
> y suma `pyotp` + `fido2` al subpackage `shared.auth`.

## Que entrega este plan

- **Schema Neon (migration 00000003)**:
  - `auth_mfa_methods`: enum `mfa_kind` (totp|email_code), preferred,
    user_id FK, secret encrypted (solo TOTP), recovery_codes_hash JSONB,
    confirmed_at, last_used_at, disabled_at.
  - `auth_webauthn_credentials`: credential_id (BYTEA UK), public_key
    BYTEA, sign_count INT, transports JSONB, attestation_format, aaguid,
    user_id FK, nickname, created_at, last_used_at.
  - `auth_webauthn_challenges`: tabla efimera de challenges (TTL via
    DELETE despues de 5 min). En realidad: usar DynamoDB con TTL en
    vez de tabla Neon — decision en seccion 1.
- **Shared subpackage `shared.auth` (extension)**: agrega `pyotp`
  + `fido2`. Modulos nuevos: `totp.py`, `webauthn.py`,
  `recovery_codes.py`. Sigue siendo UN solo portador.
- **DynamoDB nueva**: `portfolio-webauthn-challenges-${stage}` (PK
  `challenge_id`, TTL `expires_at` = 5 min). Challenges WebAuthn son
  por naturaleza efimeros y MUCHOS por segundo en uso.
- **Lambda `auth` extension** — nuevas operations:
  - `mfa.setup-totp` (genera secret + QR code) — requiere temp JWT del
    flujo `setup-mfa`.
  - `mfa.confirm-totp` (verifica primer codigo TOTP -> guarda secret).
  - `mfa.setup-email-code` (marca email-code como metodo activo).
  - `mfa.set-preferred` (cambia preferido entre los metodos activos).
  - `mfa.disable` (deshabilita un metodo; al menos uno debe quedar).
  - `mfa.recovery-codes-generate` (10 codes de 10 chars; muestra UNA vez).
  - `mfa.recovery-codes-consume` (consume 1 code -> levanta MFA bypass).
  - `webauthn.register-options` (challenge para crear credential).
  - `webauthn.register-verify` (valida attestation + guarda credential).
  - `webauthn.login-options` (challenge para login).
  - `webauthn.login-verify` (valida assertion + emite access+refresh).
  - `webauthn.list-credentials` (devuelve credentials del user).
  - `webauthn.delete-credential` (borra credential por id).
- **Login con MFA**: extiende `login.start` para devolver
  `methods` ampliado (`magic-link`, `email-code`, `totp`, `password`,
  `webauthn`) basado en `auth_mfa_methods`, `auth_credentials`,
  `auth_webauthn_credentials`. Cuando user tiene password seteada,
  `login.start` con `password=<X>` opcional valida y pide MFA si
  configurado. Nueva action: `login.verify-totp`, `login.verify-password`.

## Que NO entrega este plan

- Lambda `users` (profile, status, admin) -> **plan 03**.
- Frontend Astro de MFA setup (QR scanner, WebAuthn JS, recovery
  codes UI) -> plan futuro.
- SMS/Twilio como MFA — fuera de scope.

## Cuando leer

| Tema | Archivo |
|------|---------|
| Problema, solucion, AC numerados | [01-contexto-y-decision.md](01-contexto-y-decision.md) |
| Schema Neon extension (3 tablas nuevas) | [02-schema-neon-mfa.md](02-schema-neon-mfa.md) |
| Shared.auth extension (TOTP + WebAuthn + recovery codes) | [03-shared-auth-extension.md](03-shared-auth-extension.md) |
| Infraestructura: DynamoDB challenges + SSM nuevos | [04-infraestructura.md](04-infraestructura.md) |
| Arquitectura del Lambda auth: nuevas operations mfa + webauthn | [05-lambda-auth-extensions.md](05-lambda-auth-extensions.md) |
| Testing (unit + integration + WebAuthn fixtures) | [06-testing.md](06-testing.md) |
| Archivos afectados con verificacion por archivo | [07-archivos-afectados.md](07-archivos-afectados.md) |
| Descomposicion en tareas atomicas | [08-descomposicion-paralelizacion.md](08-descomposicion-paralelizacion.md) |
| Commits incrementales | [09-commits.md](09-commits.md) |
| Paralelizacion con git worktrees | [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) |
| Verificacion E2E iterativa | [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Estado por fase

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Plan 01 mergeado a `dev` (prerequisito) | pending (depende de 01) |
| 1 | Plan escrito + carpeta `docs/specs/02-auth-mfa/` commiteada | pending |
| 2 | Schema Neon `auth_mfa_methods` + `auth_webauthn_credentials` (migration 00000003) | pending |
| 3 | `shared.auth` extension (pyotp + fido2 + totp/webauthn/recovery_codes) | pending |
| 4 | DynamoDB `webauthn-challenges` + SSM `webauthn-encryption-key` | pending |
| 5 | Lambda `auth` operation `mfa` (setup-totp, confirm-totp, setup-email-code, set-preferred, disable) | pending |
| 6 | Lambda `auth` operation `mfa` (recovery-codes-generate, recovery-codes-consume) | pending |
| 7 | Lambda `auth` operation `webauthn` (register-options, register-verify) | pending |
| 8 | Lambda `auth` operation `webauthn` (login-options, login-verify, list, delete) | pending |
| 9 | Extension de `login.start` para detectar metodos MFA del user + nuevos `login.verify-*` (password, totp) | pending |
| 10 | Rate-limit rules nuevas + integracion + audit log events nuevos | pending |
| 11 | Verificacion E2E + actualizacion ER + limpieza spec | pending |

## Decisiones no-reabribles

1. **WebAuthn challenges en DynamoDB, NO en Neon**: los challenges
   son efimeros (5 min TTL), 1 por intento de register/login, en uso
   activo pueden ser muchos por usuario. TTL nativo + lookup O(1)
   justifican DDB. La tabla `auth_webauthn_challenges` propuesta
   originalmente se descarta.
2. **TOTP secret cifrado at-rest con KMS DataKey**: el secret de
   TOTP es un secreto sensible (permite generar codes validos). Se
   cifra con AWS KMS GenerateDataKey + AES-256-GCM antes de guardarlo
   en `auth_mfa_methods.totp_secret_ciphertext`. La envelope encryption
   key se identifica por `data_key_ciphertext` (almacenado al lado).
3. **Recovery codes: 10 codes de 10 chars Crockford, mostrados UNA vez**:
   se muestran al setear MFA exitoso por primera vez. Hash SHA-256 en
   DB (`auth_mfa_recovery_codes` tabla nueva o JSONB en
   `auth_mfa_methods.recovery_codes_hash`). Decision: tabla aparte
   `auth_mfa_recovery_codes` (id, user_id FK, code_hash UK, consumed_at
   NULL) para auditoria individual por code consumido.
4. **fido2 lib**: `python-fido2>=1.1,<2.0` (Yubico). Soporta WebAuthn
   L2 + L3 partial. Implementa validacion de attestation (`none`,
   `direct`, `indirect`, `packed`, `tpm`, `android-key`).
5. **WebAuthn RP_ID y origin**: `RP_ID = 'the-full-stack.com'`
   (matchea el apex + todos los subdomains). `expected_origin` lista
   de los 6 hostnames de prod + sus equivalentes dev/stage. En el cold
   start, leer de env var `WEBAUTHN_ALLOWED_ORIGINS`.
6. **User verification (UV)**: requerir UV=`preferred` en register,
   `required` en login (ie biometric/PIN confirm). Trade-off: algunos
   YubiKeys no tienen UV; preferimos seguridad sobre cobertura
   universal.
7. **TOTP issuer label**: `the-full-stack.com:<email>` para que el QR
   muestre nombre del sitio + email en Google/Authy. RFC 6238 standard.
8. **Login con password opcional**: `login.start` acepta `password`
   opcional en el body. Si password presente: valida ANTES de devolver
   los methods. Si match: emite temp JWT con flow=`login-mfa` step=2
   y devuelve la lista de MFA methods. Si MFA no configurado: emite
   access+refresh directo (skip MFA). Si MFA configurado: el cliente
   llama a `login.verify-totp` o `webauthn.login-verify`.
9. **Bypass MFA con recovery code**: action
   `mfa.recovery-codes-consume` acepta temp JWT del flujo login (con
   step=2 post-password) + el code. Si match: emite access+refresh y
   marca el code como consumed. NO se puede recovery-code-consume sin
   haber pasado password primero (defense in depth).
10. **Migration 00000003 forward-only en prod**: el downgrade tira
    `auth_webauthn_credentials` que puede tener data real de usuarios.
    El `downgrade()` se implementa (para branches de prueba) pero NO
    se corre en `prod` nunca.

## Reglas criticas (siempre activas)

- **SIEMPRE** TOTP secret se cifra con envelope encryption (KMS
  DataKey + AES-256-GCM) antes de persistir en Neon. NUNCA en plain
  text.
- **SIEMPRE** las recovery codes se muestran UNA sola vez (response
  de `recovery-codes-generate`). El frontend debe guardarlas. El
  backend SOLO guarda el hash SHA-256.
- **SIEMPRE** WebAuthn challenge se valida contra DDB con TTL antes de
  consumir. Single-use: tras verificar exitosa, DELETE del row.
- **SIEMPRE** sign_count se valida monotonicamente creciente. Si
  llega un sign_count <= sotrado -> rechazar (token cloning detection).
- **SIEMPRE** el flujo de MFA setup requiere el user ya autenticado
  (access JWT valido).
- **NUNCA** logear el TOTP secret, ni el plaintext del DataKey, ni el
  contenido de la cookie/credential WebAuthn.
- **NUNCA** permitir disable de TODOS los metodos MFA: si el user
  tiene `mfa.disable` para su unico metodo, devolver
  `409 MUST_KEEP_ONE_METHOD`.

## Matriz de verificacion (rapida)

| Capa | Comando |
|------|---------|
| Sintaxis Python | `python -m compileall -q serverless/lambda/services/auth serverless/lambda/shared/auth` |
| Imports shared-only | `python devtools/run.py serverless lint-deps --lambda=auth` |
| Tests unit `shared.auth` (incluye TOTP + WebAuthn + recovery) | `python devtools/run.py serverless tests --type=unit --shared` |
| Tests unit `auth` (incluye operations mfa + webauthn) | `python devtools/run.py serverless tests --type=unit --lambda=auth` |
| Migration up (dev) | `python devtools/run.py serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev` |
| Run local TOTP setup | `python devtools/run.py serverless run --stage=local --lambda=auth --event=events/mfa-setup-totp.json` |
| Deploy dev | `python devtools/run.py serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev` |
| Smoke E2E | ver [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Bibliografia interna

- Plan 01 (precursor): docs/specs/01-auth-infra-basics/ — al cierre
  estara eliminado del repo; referencia historica en `git log`.
- `.claude/docs/auth-system/` — documentacion permanente creada por
  el plan 01. Este plan agrega capitulos sobre MFA.
- `.claude/rules/lambda-controller.md`, `.claude/rules/lambda-shared-imports.md`,
  `.claude/rules/neon-management.md`, `.claude/rules/serverless-secrets.md`.
- python-fido2: https://github.com/Yubico/python-fido2 (NO fetch
  desde aqui — solo referencia).
- WebAuthn spec L2: https://www.w3.org/TR/webauthn-2/ (idem).
- pyotp: RFC 6238 / 4226.
