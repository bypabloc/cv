# 01. Contexto y decision

## 1. Contexto / Problema

El plan 01 entrego el flujo basico de auth (register/login/verify/logout)
con dos metodos de identificacion del email del usuario: magic-link y
code de 8 chars al email. Esto es suficiente para validar email pero NO
es MFA verdadero: cualquier atacante con acceso al inbox del usuario
puede tomar la cuenta.

Este plan agrega:

1. **TOTP** (RFC 6238): el clasico Google Authenticator / Authy /
   1Password. Estandar de la industria. Bajo costo ($0). Funciona
   offline. Resistente a phishing parcialmente (no protege contra
   real-time MitM con reverse proxy estilo evilginx, pero si contra
   credential stuffing y phishing pasivo).
2. **Email-code como MFA**: el mismo mecanismo del plan 01 pero
   "promovido" a 2do factor cuando el user ya esta autenticado por
   password / passkey. Util si el user pierde acceso al TOTP pero
   sigue con su email.
3. **WebAuthn / Passkeys**: el futuro. Passkey sincronizado via
   iCloud Keychain / Google Password Manager / 1Password permite
   passwordless real con phishing-resistance criptografico (origin
   binding). YubiKey hardware tambien. Soportado nativamente por
   Chrome/Edge/Safari/Firefox modernos (>97% market share 2026).

### Hallazgos de exploracion

- python-fido2 (`>=1.1`) es la lib mas mantenida (mantenida por
  Yubico). Cubre WebAuthn L2 + parcial L3 (multi-device, conditional
  UI). **Pendiente spike**: validar firma actual de `Fido2Server`
  (`register_begin`/`authenticate_begin` retornan `(options, state)`
  donde `state` es dict JSON-serializable, no bytes).
- pyotp (`>=2.9`) es trivial y standard.
- AWS KMS `kms:Encrypt`/`kms:Decrypt` con CMK directa soporta hasta
  4 KB de plaintext — el secret TOTP de 20 bytes entra de sobra. No
  hace falta envelope encryption con DataKey.
- Plan 01 dejo `auth_users` + el lambda `auth` listos para extension.
  Agregar operations `mfa` + `webauthn` es escalable (el handler ya
  enruta por operation/action).
- DDB con TTL nativo es ideal para WebAuthn challenges (5 min, single
  use, alto throughput potencial).

## 2. Solucion Propuesta

Extension del Lambda `auth`. Sin cambios estructurales — solo
agregamos:

- Modulos en `shared/auth/`: `totp.py`, `webauthn.py`,
  `recovery_codes.py`. Wrappers KMS en `shared.aws.kms`
  (`kms_encrypt`, `kms_decrypt` con `EncryptionContext`).
- Tablas Neon: `auth_mfa_methods` (1 columna BYTEA para el ciphertext
  TOTP, sin nonce ni data_key), `auth_mfa_recovery_codes`,
  `auth_webauthn_credentials`.
- DDB: `portfolio-webauthn-challenges-${stage}`.
- KMS CMK directa para el secret TOTP (`alias/portfolio-lambdas`).
- 14 nuevas actions en el lambda (entre `mfa.*` y `webauthn.*`).
- Extension de `login.start` y nuevas `login.verify-password`,
  `login.verify-totp`.

### Decisiones clave

**Decision 1: TOTP secret cifrado con KMS CMK directa (NO envelope)** —
el secret TOTP es 20 bytes random (160 bits, RFC 6238). Entra holgado
en el limite de 4 KB de `kms:Encrypt`. Llamamos
`kms:Encrypt(KeyId='alias/portfolio-lambdas', Plaintext=secret_b32_bytes,
EncryptionContext={'user_id': str(user.id), 'purpose': 'totp'})` y
guardamos UNICAMENTE el ciphertext (BYTEA) en
`auth_mfa_methods.totp_secret_ciphertext`. Para verificar:
`kms:Decrypt(CiphertextBlob=..., EncryptionContext=...)`. Razon del
cambio respecto a la version inicial del plan (envelope con DataKey
por user): la envelope encryption no aporta seguridad adicional
sobre CMK directa con `EncryptionContext` — el CMK sigue siendo el
unico punto de compromiso. Bajo costo (~$0.03 por 10000 `kms:Decrypt`,
cacheable in-memory dentro del cold start del Lambda con TTL 5 min).
Schema mas chico (1 columna vs 3), 1 sola llamada KMS por op (vs 1
`GenerateDataKey` + 1 `Decrypt` por verify), sin manejo de nonce ni
AESGCM en codigo propio.

**Decision 2: recovery codes en tabla separada** —
`auth_mfa_recovery_codes (id, user_id, code_hash UNIQUE, consumed_at)`
permite auditar consumo individual y agregar audit log
"recovery_code.consumed". 10 codes generados al primer
`mfa.recovery-codes-generate`; el user puede regenerar (descarta los
viejos, emite 10 nuevos) con `mfa.recovery-codes-generate` de nuevo.

**Decision 3: login flow con password opcional** —
`login.start` body acepta `{email, cf_turnstile_response, password?}`:

- Si `password` ausente: comportamiento del plan 01 (envia
  magic-link/code, devuelve methods).
- Si `password` presente y match: evalua MFA:
  - Si user NO tiene MFA -> emite access+refresh directo.
  - Si user TIENE MFA -> emite temp JWT step=2 con claim
    `prev=password` + `methods=[totp, webauthn]`. Cliente llama
    `login.verify-totp` / `webauthn.login-verify` /
    `mfa.recovery-codes-consume`. NUNCA incluye `email-code` en
    `methods` post-password (decision 10 — recovery solo
    post-password/webauthn).

**Decision 4: WebAuthn con RP_ID = apex** — `the-full-stack.com` como
RP ID permite que cualquier subdomain (`hub.portfolio.the-full-stack.com`,
`fintech...`, etc.) use la misma credencial. WebAuthn requiere que el
RP_ID sea sufijo del origin. Para dev/stage que usan
`portfolio.dev.the-full-stack.com`, el RP_ID es
`portfolio.dev.the-full-stack.com` (configurable por env).

**Decision 5: challenges en DynamoDB con TTL** — cada
`webauthn.register-options` y `webauthn.login-options` genera un
challenge (16 bytes random), lo guarda en DDB con TTL=5min, y devuelve
al frontend. Cuando llega `webauthn.*-verify`, lee + valida + DELETE
del challenge. PK = `challenge_id` (UUIDv7 string). Atributos:
`user_id`, `kind` (`register|login`), `expires_at`.

**Decision 6: sign_count monotonico** — el WebAuthn standard pide
guardar el `sign_count` y validar que la nueva assertion lo trae mayor
que el guardado. Si llega menor o igual -> rechazar (token clonado).
Tabla `auth_webauthn_credentials.sign_count INT NOT NULL DEFAULT 0`,
update en cada login-verify exitoso.

**Decision 7: WebAuthn user verification (UV) required en login** —
`UserVerificationRequirement.REQUIRED` en login-options. En register,
`PREFERRED`. Trade-off: algunos YubiKeys hardware-only (sin biometric)
fallan en login si no soportan UV; pero la seguridad lo justifica.

**Decision 8: backup MFA = recovery codes** — si user pierde
TOTP/WebAuthn devices, debe poder usar 1 de los 10 recovery codes. NO
implementamos email-only-recovery flow (riesgo: si email se hackea, MFA
queda bypassed). Recovery codes son el unico bypass.

## 3. Criterios de Aceptacion (AC)

### MFA TOTP

- **AC-1**: Given un user autenticado (access JWT valido) sin TOTP
  configurado, When llama `POST /auth operation=mfa action=setup-totp`,
  Then la response trae: `{secret_b32, otpauth_url}` (sin
  `qr_code_svg` — el frontend renderiza el QR del `otpauth_url`) y
  guarda un row `auth_mfa_methods` con `kind=totp`,
  `confirmed_at=NULL`. El secret se cifra con `kms:Encrypt`
  (`EncryptionContext={user_id, purpose:totp}`) antes de persistir.

- **AC-2**: Given un row TOTP pendiente confirmacion (confirmed_at=NULL),
  When llama `mfa.confirm-totp` con `code=<6-digit>` correcto, Then
  marca `confirmed_at=now()` y `auth_mfa_methods.preferred=true` si era
  el primer metodo. Devuelve 204.

- **AC-3**: Given un row TOTP confirmado, When llama
  `mfa.confirm-totp` con code incorrecto 3 veces, Then la 3ra devuelve
  `400 INVALID_TOTP_CODE` y registra audit log
  `mfa.confirm-totp.failed`.

- **AC-4**: Given un user con TOTP configurado, When llama
  `mfa.set-preferred` con `kind=email_code`, Then actualiza
  `auth_mfa_methods.preferred=false` en el TOTP row y `=true` en el
  email_code row.

- **AC-5**: Given un user con `total_mfa == 1` (un solo metodo MFA
  considerando `auth_mfa_methods` activos + `auth_webauthn_credentials`
  activos), When llama `mfa.disable` con ese metodo, Then devuelve
  `409 MUST_KEEP_ONE_MFA_METHOD`. La cuenta es transversal (mismo
  principio que AC-17).

- **AC-5b**: Given un user A, When intenta `mfa.disable` con `kind`
  que existe SOLO para user B, Then devuelve `404 NOT_FOUND` (sin
  revelar la existencia ajena — simetria con AC-25).

- **AC-6**: Given un user con `total_mfa >= 2`, When llama
  `mfa.disable` con uno de ellos, Then marca `disabled_at=now()` y si
  era el preferred, asciende otro a preferred (FIFO por
  `confirmed_at`).

### Recovery codes

- **AC-7**: Given un user con MFA recien confirmado, When llama
  `mfa.recovery-codes-generate`, Then genera 10 codes
  `[A-HJ-NP-Z2-9]{10}` y devuelve la lista UNA vez. Guarda los 10
  hashes en `auth_mfa_recovery_codes`.

- **AC-8**: Given un user que ya tiene 10 codes activos, When llama
  `mfa.recovery-codes-generate` de nuevo, Then borra los 10 viejos
  (DELETE rows) y emite 10 nuevos. Audit log
  `mfa.recovery-codes.regenerated`.

- **AC-9**: Given un user con MFA configurado + temp JWT step=2 con
  claim `prev=password` (o `prev=webauthn`), When llama
  `mfa.recovery-codes-consume` con un code valido, Then marca
  `consumed_at=now()` y emite access+refresh JWT. Devuelve
  `200 {access_token, refresh_token, ...}`.

- **AC-9b**: Given un temp JWT step=2 con `prev=magic-link` o
  `prev=email-code`, When llama `mfa.recovery-codes-consume`, Then
  devuelve `403 RECOVERY_REQUIRES_STRONG_FACTOR` (defense in depth —
  decision 10).

- **AC-10**: Given un recovery code ya consumido, When se intenta
  consumir de nuevo, Then devuelve `400 RECOVERY_CODE_CONSUMED`.

### WebAuthn / Passkeys

- **AC-11**: Given un user autenticado, When llama
  `webauthn.register-options`, Then devuelve la lista de parametros
  WebAuthn (challenge b64, rp_id, user.id, user.name, pubKeyCredParams,
  excludeCredentials, attestation='none', authenticatorSelection,
  timeout=300000). Guarda challenge en DDB con TTL 5min.

- **AC-12**: Given el frontend completo el WebAuthn ceremony con
  navigator.credentials.create(), When llama `webauthn.register-verify`
  con `{attestation_response, client_data_json, attestation_object}`,
  Then valida attestation, guarda
  `auth_webauthn_credentials(user_id, credential_id, public_key,
  sign_count=0, transports, ...)`, borra el challenge de DDB,
  devuelve `201 {credential_id, nickname}`.

- **AC-13**: Given un user con >=1 credential WebAuthn, When llama
  `webauthn.login-options` con `email=<X>`, Then devuelve `{challenge,
  allowCredentials=[{id, type, transports}, ...]}`. Guarda challenge en
  DDB.

- **AC-14**: Given el frontend completa
  navigator.credentials.get(), When llama `webauthn.login-verify` con
  `{assertion_response}`, Then valida assertion (signature contra
  public_key, sign_count > stored), actualiza `sign_count`, borra
  challenge, emite access+refresh JWT, audit log
  `webauthn.login.success`.

- **AC-15**: Given un assertion con `sign_count` <= stored, When se
  procesa `webauthn.login-verify`, Then devuelve
  `401 WEBAUTHN_CLONE_DETECTED`, audit log
  `webauthn.login.clone_detected`, Y marca el credential
  `disabled_at=now()` SIEMPRE (no opcional — decision 14). La
  reactivacion solo via endpoint admin futuro.

- **AC-16**: Given un user con N credentials, When llama
  `webauthn.list-credentials`, Then devuelve la lista
  `[{credential_id, nickname, created_at, last_used_at, transports}, ...]`
  ordenada por last_used_at DESC.

- **AC-17**: Given un user con `total_mfa = N` (suma de
  `auth_mfa_methods` activos confirmados + `auth_webauthn_credentials`
  activos), When llama `webauthn.delete-credential` con un
  credential_id valido, Then:
  - si `total_mfa - 1 >= 1` -> DELETE del row + 204.
  - si `total_mfa - 1 == 0` -> `409 MUST_KEEP_ONE_MFA_METHOD`
    (el user no se queda sin MFA).
  La cuenta es transversal: un user con 1 TOTP + 1 passkey puede
  borrar el passkey (le queda TOTP). Un user con 2 passkeys y nada mas
  puede borrar 1. Solo si la operacion deja al user en 0 metodos
  totales se bloquea. Mismo principio aplica a `mfa.disable` (AC-5
  reescrito).

### Login con MFA

- **AC-18**: Given un user con password seteada + TOTP configurado,
  When llama `login.start` con `{email, password, cf_turnstile}`, Then
  valida password con argon2.verify. Si match: emite temp JWT
  flow=`login-mfa` step=2 + devuelve `{methods: ['totp',
  'webauthn']}`. NO emite access+refresh aun.

- **AC-19**: Given el step 2 del login (temp JWT step=2), When llama
  `login.verify-totp` con `code` correcto, Then emite access+refresh.

- **AC-20**: Given un user sin MFA, When llama `login.start` con
  password correcta, Then emite access+refresh directo (skip step 2).

- **AC-21**: Given un user con password seteada, When llama
  `login.start` con password INCORRECTA, Then incrementa
  `failed_attempts`, devuelve `401 INVALID_PASSWORD`, NO revela si el
  email existe o no (en este caso ya existe, pero el response es
  identico al de email no encontrado en cuanto a info filtrable). El
  rate-limit aplica por IP (no por user_id) para evitar enumeration
  via timing — decision 13.

- **AC-22**: Given un user con password + MFA + recovery codes, When
  el user llama `mfa.recovery-codes-consume` con un code valido tras
  pasar password (temp JWT step=2 `prev=password`), Then emite
  access+refresh y marca el code consumed. AC-9 reforzada.

### Migration

- **AC-23**: Given la migration `00000003_auth_mfa.py` aplicada en un
  branch Neon de prueba, When se ejecuta `downgrade -1` y luego
  `upgrade head`, Then el schema vuelve al de plan 01 y se recrean
  las 3 tablas `auth_mfa_*` + `auth_webauthn_credentials` sin error.

### Seguridad

- **AC-24**: Given que el TOTP secret se persiste en
  `auth_mfa_methods`, When se inspecciona la fila en Neon, Then NUNCA
  aparece el secret en plain — solo `totp_secret_ciphertext` (BYTEA,
  output de `kms:Encrypt` con CMK `alias/portfolio-lambdas` +
  `EncryptionContext={user_id, purpose:totp}`). Sin columnas
  `nonce` ni `data_key_ciphertext` (decision 1).

- **AC-25**: Given una request con access JWT de un user, When intenta
  llamar `webauthn.delete-credential` con un credential_id de OTRO
  user, Then devuelve `404 NOT_FOUND` (no `403 FORBIDDEN` para evitar
  enumeration).

- **AC-26**: Given un passkey registrado en env `dev` (RP_ID
  `portfolio.dev.the-full-stack.com`), When el browser intenta
  `webauthn.login-options` en `prod` (origin
  `the-full-stack.com`), Then la lista `allowCredentials` queda vacia
  y `navigator.credentials.get()` falla en el cliente. Los passkeys
  NO migran entre envs (decision 5). Test E2E lo demuestra con
  fixtures separados de SoftWebauthnDevice por env.

- **AC-27**: Given un user con MFA recien confirmado (primera vez —
  transicion de 0 metodos a 1), When `mfa.confirm-totp` o
  `webauthn.register-verify` retorna OK, Then se revoca la familia
  de refresh tokens activa del user (mismo efecto que
  `session.logout-all`). El proximo `/session/refresh` con el
  refresh anterior devuelve `401 TOKEN_FAMILY_REVOKED`. Razon:
  cerrar la ventana donde un atacante con refresh previo seguiria
  operando sin pasar MFA (decision 15).
