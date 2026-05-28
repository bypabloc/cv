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

- **Schema Neon (migration 00000003)** — 3 tablas nuevas:
  - `auth_mfa_methods`: enum `mfa_kind` (totp|email_code), preferred,
    user_id FK, `totp_secret_ciphertext` (BYTEA, KMS-encrypted via CMK
    directa — NO envelope), confirmed_at, last_used_at, disabled_at.
  - `auth_mfa_recovery_codes`: tabla aparte con `user_id`, `code_hash`
    UK, `consumed_at`. Auditoria individual por code.
  - `auth_webauthn_credentials`: credential_id (BYTEA UK), public_key
    BYTEA, sign_count INT, transports JSONB, attestation_format, aaguid,
    user_id FK, nickname, created_at, last_used_at, disabled_at.
- **Shared subpackage `shared.auth` (extension)**: agrega `pyotp`
  + `python-fido2`. Modulos nuevos: `totp.py`, `webauthn.py`,
  `recovery_codes.py`. NO `encryption.py` (envelope encryption se
  descarto a favor de KMS CMK directa — el secret TOTP de 20 bytes
  entra en el limite de 4KB de `kms:Encrypt`). Sigue siendo UN solo
  portador.
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

Mapeo 1:1 con las 12 tareas (T1..T12) de [08-descomposicion-paralelizacion.md](08-descomposicion-paralelizacion.md)
y los 8 PRs de [09-commits.md](09-commits.md).

| Fase | Tarea | PR | Descripcion |
|------|-------|----|-------------|
| 0 | — | — | Plan 01 mergeado a `dev` (prerequisito) |
| 1 | T1 | PR 1 | Plan + docs/claude permanentes (NO catalogo de portadores aun) |
| 2 | T2 + T3 | PR 2 | `shared.auth` ext (pyotp + fido2 + recovery_codes) + `shared.aws` KMS wrappers + catalogo |
| 3 | T4 | PR 3 | Schema Neon (migration 00000003) + modelos + repositories |
| 4 | T5 + T6 | PR 4 | DynamoDB `webauthn-challenges` + manifest update (IAM kms) |
| 5 | T7 + T8 | PR 5 | Lambda `auth`: services internos + EventModel + Pydantic models |
| 6 | T9 + T10 | PR 6 | Controllers `mfa.*` + `webauthn.*` (worktrees paralelos) |
| 7 | T11 | PR 7 | Login extension: verify-password + verify-totp + login.start delta + rate-limit + deploy dev |
| 8 | T12 | PR 8 | Verificacion E2E + integration tests + ER + cleanup carpeta spec |

## Decisiones no-reabribles

1. **WebAuthn challenges en DynamoDB, NO en Neon**: los challenges
   son efimeros (5 min TTL), 1 por intento de register/login, en uso
   activo pueden ser muchos por usuario. TTL nativo + lookup O(1)
   justifican DDB. La tabla `auth_webauthn_challenges` propuesta
   originalmente se descarta.
2. **TOTP secret cifrado at-rest con KMS CMK directa (sin envelope)**:
   el secret TOTP de 20 bytes entra holgado en el limite de 4 KB de
   `kms:Encrypt`. Llamamos `kms:Encrypt` con la CMK
   `alias/portfolio-lambdas` + `EncryptionContext={user_id, purpose:totp}`
   y guardamos UNICAMENTE `totp_secret_ciphertext` (BYTEA) en
   `auth_mfa_methods`. Sin envelope encryption, sin DataKey por user,
   sin `nonce`/`data_key_ciphertext`. Trade-off: cada
   `verify-totp` llama a `kms:Decrypt` (cacheable in-memory dentro
   del Lambda con TTL 5 min para no martillar KMS). Razon del cambio:
   envelope encryption con DataKey-por-user no aporta seguridad
   adicional sobre CMK directa con encryption-context (el CMK sigue
   siendo el unico punto de compromiso) y agrega ~30% mas de codigo
   + 2 columnas + latencia adicional.
3. **Recovery codes: 10 codes de 10 chars Crockford, mostrados UNA vez**:
   se muestran al setear MFA exitoso por primera vez. Hash SHA-256 en
   DB en tabla aparte `auth_mfa_recovery_codes` (`id`, `user_id` FK,
   `code_hash` UK, `consumed_at` NULL) para auditoria individual por
   code consumido. NUNCA en JSONB de `auth_mfa_methods`.
4. **fido2 lib**: `python-fido2>=1.1,<2.0` (Yubico). Soporta WebAuthn
   L2 + L3 partial. Implementa validacion de attestation (`none`,
   `direct`, `indirect`, `packed`, `tpm`, `android-key`). **Spike
   obligatorio en T2** (commit 2.2 — antes de redactar el codigo
   final): validar firma actual de `Fido2Server.register_begin` /
   `register_complete` / `authenticate_begin` / `authenticate_complete`
   (state es `dict` JSON-serializable, no `bytes`). Si la firma
   difiere, ajustar `shared.auth.webauthn` y `ChallengeService`.
5. **WebAuthn RP_ID por env (passkeys no migran)**: en `prod`
   `RP_ID=the-full-stack.com` (apex cubre los 6 subdomains). En `dev`
   `RP_ID=portfolio.dev.the-full-stack.com`. En `stage` idem con
   `stage`. **Consecuencia explicita**: un passkey registrado en
   `dev` NO funciona en `prod` (RP_ID es sufijo del origin, distinto
   por env). Se acepta como diseno — un passkey por env. Los tests
   E2E lo cubren en AC-26.
6. **User verification (UV)**: requerir UV=`preferred` en register,
   `required` en login (ie biometric/PIN confirm). Trade-off: algunos
   YubiKeys no tienen UV; preferimos seguridad sobre cobertura
   universal.
7. **TOTP issuer label**: `the-full-stack.com:<email>` para que el QR
   muestre nombre del sitio + email en Google/Authy. RFC 6238 standard.
8. **QR del TOTP lo renderiza el frontend (NO el backend)**: el
   Lambda devuelve solo `secret_b32` + `otpauth_url`; el cliente
   renderiza el QR con `qrcode` JS (~5KB gzipped). Razon: evita una
   dep mas en `shared.auth` (`segno`), reduce ~3-5 KB por response,
   y mantiene el Lambda mas chico (mejor cold start). El AC-1 refleja
   el contrato actual.
9. **Login con password opcional**: `login.start` acepta `password`
   opcional en el body. Si password presente: valida ANTES de devolver
   los methods. Si match: emite temp JWT con flow=`login-mfa` step=2
   y devuelve la lista de MFA methods. Si MFA no configurado: emite
   access+refresh directo (skip MFA). Si MFA configurado: el cliente
   llama a `login.verify-totp` o `webauthn.login-verify`.
10. **Bypass MFA con recovery code SOLO post-password o post-webauthn**:
    `mfa.recovery-codes-consume` exige temp JWT step=2 con claim
    `prev=password` o `prev=webauthn`. NUNCA acepta step=2 con
    `prev=magic-link` o `prev=email-code` (ambos son verificables con
    acceso al email — permitir recovery-bypass desde ahi anularia
    el segundo factor). Defense in depth.
11. **Migration 00000003 forward-only en prod**: el downgrade tira
    `auth_webauthn_credentials` que puede tener data real de usuarios.
    El `downgrade()` se implementa (para branches de prueba) pero NO
    se corre en `prod` nunca.
12. **`provisioner.py` para `uses.kms`: spike-first**: si el manifest
    actual NO soporta el bloque `uses.kms` declarativo, T6 se hace
    DENTRO de este plan (1 commit chico). Si el cambio requiere
    refactor mayor del provisioner (>200 lineas, tests propios),
    se saca a un plan devtools-aparte y T6 se reemplaza por una
    inline policy declarada en el shape ya soportado. **Antes de
    PR 4** se decide cual de los dos. La decision queda anotada en
    el body del PR 4.
13. **`shared.rate_limit` custom keys (`user_id` en vez de IP)**:
    se saca de este plan. Si hoy `shared.rate_limit` SOLO soporta
    rate-limit por IP, todas las reglas MFA usan IP. Soporte para
    custom keys es un plan separado. **Consecuencia**: AC del rate
    limit usan IP, no user_id (ver seccion 04 actualizada). Evita
    enumeration de emails via timing del rate-limit.
14. **Clone detection (sign_count regresion) -> disable obligatorio**:
    AC-15 sin "opcional". Al detectar `new <= stored`, el credential
    se marca `disabled_at=now()` y se loggea
    `webauthn.login.clone_detected`. La reactivacion solo por endpoint
    admin (futuro plan 03 / users-management).
15. **Sesiones activas tras setup TOTP/WebAuthn**: cuando el user
    habilita su PRIMER metodo MFA confirmado, se revoca la familia de
    refresh tokens activa del user (igual que `session.logout-all`).
    El frontend recibe `401` en el proximo refresh y obliga a re-login
    con MFA. Se documenta como AC-27. Razon: cerrar la ventana donde
    un atacante con refresh previo seguiria operando sin pasar MFA.

## Reglas criticas (siempre activas)

- **SIEMPRE** TOTP secret se cifra con `kms:Encrypt` (CMK directa
  `alias/portfolio-lambdas` + `EncryptionContext={user_id, purpose:totp}`)
  antes de persistir. NUNCA en plain text. NUNCA envelope encryption
  con DataKey-por-user.
- **SIEMPRE** las recovery codes se muestran UNA sola vez (response
  de `recovery-codes-generate`). El frontend debe guardarlas. El
  backend SOLO guarda el hash SHA-256.
- **SIEMPRE** WebAuthn challenge se valida contra DDB con TTL antes de
  consumir. Single-use: tras verificar exitosa, DELETE del row.
- **SIEMPRE** sign_count se valida monotonicamente creciente. Si
  llega un sign_count <= stored -> rechazar Y marcar el credential
  `disabled_at=now()` (clone detection, decision 14).
- **SIEMPRE** el flujo de MFA setup requiere el user ya autenticado
  (access JWT valido).
- **SIEMPRE** tras confirmar el PRIMER metodo MFA, revocar la familia
  de refresh tokens activa del user (decision 15 / AC-27).
- **SIEMPRE** `mfa.recovery-codes-consume` exige temp JWT con
  `prev=password` o `prev=webauthn`. NUNCA `prev=magic-link` ni
  `prev=email-code` (decision 10).
- **SIEMPRE** rate-limit de auth se aplica por IP (decision 13);
  custom keys por `user_id` quedan fuera de scope.
- **NUNCA** logear el TOTP secret (ni `secret_b32` plaintext ni el
  resultado de `kms:Decrypt`), ni el contenido de la cookie/credential
  WebAuthn.
- **NUNCA** permitir disable de TODOS los metodos MFA del user. Si
  `mfa.disable` o `webauthn.delete-credential` dejaria al user con 0
  metodos MFA totales (suma de `auth_mfa_methods` activos +
  `auth_webauthn_credentials` activos), devolver
  `409 MUST_KEEP_ONE_MFA_METHOD`. La cuenta se hace sobre TODOS los
  metodos del user, no por tipo.

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
