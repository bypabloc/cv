# Sistema de autenticacion del portfolio

> Reglas duras para trabajar con el Lambda `auth`, el subpackage
> `shared.auth`, el schema `auth_*` en Neon, la tabla DDB `jwt-blacklist`
> y los flujos login/verify/session. El alta ocurre dentro del flujo `login`
> unico (`login.start` crea el pending); la operation `register` fue
> ELIMINADA. El email transaccional lo envia el Lambda `send_email` (invocado
> async, sin SQS). Aplica al backend serverless. NO aplica al frontend Astro
> ni al dashboard Next.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Cualquier archivo bajo `serverless/lambda/services/auth/`
  (incluye `core/controllers/{mfa,webauthn}` y los services
  `{mfa_method,totp,webauthn,challenge,recovery_codes,session}_service.py`)
- Cualquier archivo bajo `serverless/lambda/services/users/` (Lambda
  `users` del plan 03: profile / status / admin)
- Cualquier archivo bajo `serverless/lambda/shared/auth/`
  (incluye `{totp,webauthn,recovery_codes,admin}.py`)
- `serverless/lambda/shared/aws/kms.py`
- Cualquier archivo bajo `serverless/lambda/shared/db/models/auth/`
  (incluye `{mfa_method,recovery_code,webauthn_credential,user_session,
  admin_action,consent_log}.py`)
- `serverless/lambda/shared/db/repositories/auth.py` +
  `serverless/lambda/shared/db/repositories/auth_mfa.py` +
  `serverless/lambda/shared/db/repositories/auth_users.py`
- `serverless/lambda/shared/db/alembic/versions/*auth*` (incluye
  `00000003_auth_mfa.py` y `00000004_auth_users_extension.py`)
- `serverless/lambda/resources/dynamodb/jwt-blacklist.yaml`
- `serverless/lambda/resources/dynamodb/webauthn-challenges.yaml`
- `serverless/lambda/resources/secrets/jwt-secret.yaml` +
  `serverless/lambda/resources/secrets/admin-emails.yaml`
- Cualquier referencia a `/portfolio/${stage}/jwt-secret` en SSM
- Decisiones sobre JWT (HS256, lifetimes, claims, family_id, rotation)
- Decisiones sobre rate-limit de los endpoints `/auth?operation=...`
- Decisiones sobre MFA (TOTP, email-code, recovery codes, WebAuthn /
  passkeys, sign_count, RP_ID, cifrado KMS del TOTP secret)

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

### Login UX (modelo de lista de metodos)

> Plan login-mfa-list-redesign: el login muestra la **lista de factores
> `required`** del user y se completan **en cualquier orden**; los tokens
> salen SOLO cuando no quedan pendientes. La `password` es **un factor mas de
> la lista** (no un gate previo); el `passwordless` (code/magic-link al email)
> es el factor **por defecto** (`required` cuando es el unico). El motor es
> `_mfa_login.decide_mfa_step(satisfied, required)`.

- **SIEMPRE** `login.start` resuelve el user por el **`sub` del temp precheck**
  (`flow='login'` step=0 en `Authorization`), NO por el email del body. Sin
  un precheck valido -> `401 MISSING_PRECHECK`. El email solo va en el body
  en el UNICO caso de ALTA (email nuevo, `sub` placeholder que no resuelve
  user); el email NUNCA viaja en el JWT.
- **SIEMPRE** `login.start` de un user **active** abre el checklist: emite un
  temp `login-mfa` step=2 + `methods = required_methods()` (los factores a
  completar) + `mfa_complete:false`. Ya NO valida password (es un factor de
  la lista, se verifica con `login.verify-password`).
- **SIEMPRE** un email inexistente (alta fusion register->login) CREA el user
  `pending` con el `email` del body + envia el email unificado
  (`created:true`, `methods:['passwordless']`). Un `pending` re-emite el email
  (`created:false`).
- **SIEMPRE** `login.start` de un user `disabled`/`locked` devuelve
  `404 {error:'EMAIL_NOT_FOUND', suggest_register:false}` (anti-enumeration).
- **NUNCA** `login.start` recibe la password ni el email para un user
  existente: la password es un factor del checklist; el email se resuelve por
  el `sub`.

#### `login.check-email` (precheck + lista de metodos)

- **SIEMPRE** `login.check-email` expone, de un email **active**: que existe +
  `has_password` (bool) + **`methods_required`** (la lista de factores que el
  user marco `required`, con su config minima de render por metodo
  `{type, input, dispatch_action, sent}`) + el `temp_token` precheck.
- **TRADE-OFF ACEPTADO por el dueno del producto** (decision del plan
  login-mfa-list-redesign): `check-email` **revela** `methods_required` ANTES
  de autenticar (el front necesita la lista para montar el checklist). Esto
  INVIERTE la regla previa "NUNCA revela la lista de metodos MFA". La
  existencia del email + `has_password` ya eran enumerables; la lista de
  factores se agrega deliberadamente. **NO reabrir** sin el dueno del producto.
- **SIEMPRE** `methods_required` viene en orden fijo (`password`,
  `passwordless`, `totp`, `email_code`, `webauthn`) y trae **minimo 1**
  factor (el invariante ">=1 required" garantizado por el fallback
  `passwordless`).
- **NUNCA** `check-email` devuelve `methods_required` para un user `pending`
  (aun no tiene MFA), inexistente (alta) o `unavailable`.
- **SIEMPRE** un email `disabled`/`locked`/`deleted` (o inexistente)
  devuelve `unavailable` (mismo body), SIN `temp_token` ni `methods_required`.
  El audit log registra el estado real.
- **SIEMPRE** `login.check-email` es el UNICO punto del flujo de login con
  Turnstile + emite el `temp_token` precheck (`flow='login'` step=0) para los
  casos que continuan a `login.start` (active, pending, email nuevo con `sub`
  placeholder). NUNCA lo emite para `unavailable`.

#### Factores de la lista + actions de verificacion

- **SIEMPRE** los 5 factores del modelo de lista son: `password`,
  `passwordless` (code O magic-link al email), `totp`, `email_code`,
  `webauthn`. Cada uno se verifica con su action y suma el factor a los
  `satisfied`; `decide_mfa_step` emite los faltantes o access+refresh:

  | Factor | Action(s) de verificacion | Satisfied |
  |---|---|---|
  | `password` | `login.verify-password` (temp step=2 + password) | `'password'` |
  | `totp` | `login.verify-totp` (temp step=2 + code 6 dig) | `'totp'` |
  | `passwordless` / `email_code` | `login.send-email-code` (envia) -> `login.verify-code` (temp step=2 + code 8) | `'passwordless'`/`'email_code'` |
  | `webauthn` | `webauthn.login-options` -> `webauthn.login-verify` | `'webauthn'` |
  | recovery (escape) | `mfa.recovery-codes-consume` (temp step=2 + code 10) | saltea TODO |

- **SIEMPRE** el `temp_token` del checklist es **rolling**: cada verify emite
  uno nuevo (con el factor satisfecho codificado en el `flow` CSV) y
  blacklistea el anterior. El cliente DEBE usar el nuevo o da
  `TOKEN_BLACKLISTED`.
- **SIEMPRE** `login.verify-code`/`verify-magic-link` ramifican por
  `claims.step`: step=1 (entrada passwordless: tokens directo si el user no
  tiene mas required) vs step=2 (factor del checklist: delega en
  `decide_mfa_step`). Un user active con required NO se saltea los required
  via code/magic-link.
- **SIEMPRE** `login.send-email-code` (temp step=2) genera+envia el code
  on-demand y NO blacklistea el temp (el checklist sigue abierto).
- **SIEMPRE** el recovery code (cualquier step=2 `login-mfa`) saltea todos los
  required (anti-lockout). Decision: cualquier factor habilita el recovery
  (sin distincion fuerte/debil).

#### Flujo de entrada unico: el alta ocurre dentro de `login`

- **SIEMPRE** el flujo de entrada es `login` unico: `login.start` crea el
  user `pending` si el email no existe. `login.verify-code` /
  `login.verify-magic-link` cierran la transicion `pending -> active` segun el
  STATUS del user. El mismo `login` cubre alta y entrada.
- **SIEMPRE** la operation `register` fue ELIMINADA (plan remove-register):
  no hay controllers, models ni el kind `register` en los enums DB
  (`auth_code_kind`/`auth_link_kind` quedan en `login`/`password_reset`,
  migration 00000007). Un request `{operation:'register'}` da error de
  operation desconocida (4xx).
- **NUNCA** asumir una operation `register`: el frontend entra siempre por
  `login`; lo relevante es el STATUS del user, no la operation. (No confundir
  con `webauthn.register-options`/`register-verify`, que son el enroll de
  passkeys/MFA y SIGUEN existiendo.)

### Metodos `required` (factores exigidos al loguear)

- **SIEMPRE** un user puede marcar 1+ factores como `required`. El login los
  EXIGE TODOS (no es "cualquiera de N": es "todos los marcados"),
  completandolos en cualquier orden (`decide_mfa_step`).
- **SIEMPRE** la `password` es un factor mas: su flag `required` vive en la
  columna `auth_credentials.required` (bool, default `true` — migration
  `00000006`). Si el user tiene password, se exige por defecto.
  `MfaMethodService.required_methods()` antepone `'password'` si esta
  required.
- **SIEMPRE** el `passwordless` (code/magic-link al email) es el factor por
  DEFECTO: `required_methods()` lo agrega como fallback cuando el user no
  tiene ningun otro factor required. Garantiza el invariante "siempre >=1
  required" (un user recien registrado entra passwordless; si vuelve, vuelve
  a pedir passwordless porque es lo unico disponible).
- **SIEMPRE** el invariante ">=1 required" lo garantiza el sistema (el
  fallback `passwordless`), NO un 409: desmarcar la password
  (`security.password-set-required {required:false}`) SIEMPRE es seguro — el
  user queda con sus otros factores required o con passwordless. No hay forma
  de quedar sin via de entrada.
- **SIEMPRE** el fallback anti-lockout adicional es el **recovery code**:
  consumir un recovery code (cualquier temp step=2 `login-mfa`) SALTEA todos
  los required. Decision: cualquier factor habilita el recovery (sin
  distincion fuerte/debil).
- **SIEMPRE** las actions del modelo de lista son:

  | Action | Que hace |
  |---|---|
  | `login.check-email` | precheck: existencia + `has_password` + `methods_required` |
  | `login.start` | abre el checklist (user active) o el alta (email nuevo) |
  | `login.send-email-code` | envia el code del factor `passwordless`/`email_code` (temp step=2) |
  | `login.verify-password` | verifica la password como factor de la lista |
  | `mfa.set-required` | marca/desmarca un metodo MFA (totp/email_code) como `required` |
  | `webauthn.set-required` | marca/desmarca un passkey como `required` |
  | `security.password-set-required` | marca/desmarca la PASSWORD como `required` (auth_credentials.required) |
  | `security.overview` | resumen de metodos (estado + `required` REAL, incl. password) |

- **SIEMPRE** `security.overview` refleja el `required` REAL de la password
  (lee `auth_credentials.required`), ya NO hardcoded `false`.
- **NUNCA** un user queda sin via de entrada: el fallback `passwordless` +
  el guard transversal `MUST_KEEP_ONE_MFA_METHOD` (para el disable de un
  metodo) + el escape de recovery codes lo garantizan.

### Turnstile y rate-limit

- **SIEMPRE** Turnstile SOLO en el endpoint **inicial** (step 0) del flujo de
  auth: `login.check-email` (es el unico punto de entrada; el alta tambien
  pasa por aqui). El token de Turnstile es single-use: validarlo dos veces en
  el mismo flujo da `timeout-or-duplicate`. Ningun otro endpoint lo valida.
- **NUNCA** un endpoint **no-inicial** (step != 0) valida Turnstile. La
  autorizacion de esos endpoints es un JWT (access) o un JWT temporal
  (rolling temp del flujo). En particular `login.start` ya NO valida
  Turnstile: EXIGE el temp JWT precheck (`flow='login'` step=0) emitido por
  `login.check-email` en el header `Authorization`; sin el -> `401
  MISSING_PRECHECK`. `login.start` resuelve el user por el `sub` del precheck
  (NO compara contra un email del body; el user resuelto ES el del sub ->
  anti-cross-account inherente). Para un email nuevo (alta fusionada) el
  precheck lleva un `sub` placeholder que no resuelve user y `login.start`
  crea el pending con el `email` del body.
- **SIEMPRE** la auto-blacklist anti-solver se alimenta solo por el endpoint
  con Turnstile (`login.check-email`): el `brought_turnstile_token=True` se
  cuenta por `(ip, endpoint, window)`.
- **SIEMPRE** rate-limit per-IP via `shared.rate_limit.check_or_raise`
  con las reglas seedeadas (ver
  [.claude/docs/auth-system/03-rate-limit-rules.md](../docs/auth-system/03-rate-limit-rules.md)).
- **SIEMPRE** la verificacion de Turnstile + rate-limit ocurre ANTES
  de tocar Neon o de invocar `send_email`.

### Email async (invoke send_email)

- **SIEMPRE** el Lambda `auth` (y `users`) invoca el Lambda `send_email`
  async (`InvocationType='Event'`) para enviar email transaccional. NUNCA
  llama SES directo ni usa SQS.
- **SIEMPRE** el payload del invoke es
  `{operation:'email', action:'send', data:{kind, to:[to], data:{...}}}`.
- **SIEMPRE** el Lambda `send_email` resuelve el envio: lee la config del
  remitente de la tabla DynamoDB `email-config`, baja el template del
  bucket S3, lo renderiza con Jinja2 y envia por SES.
- **SIEMPRE** el invoke es best-effort: un fallo al invocar `send_email`
  NO rompe el request del flujo (login/verify/...) — degrada a un
  log de warning. El audit log de auth (`auth_audit_log`) lo escribe el
  Lambda `auth`, NO `send_email`.
- **NUNCA** publicar a una cola SQS para emails de auth ni mantener un
  Lambda worker SQS-consumer — el modelo es invoke directo a `send_email`.

### IAM y costos

- **SIEMPRE** el Lambda `auth` tiene IAM scoped: las tablas DDB declaradas
  en `manifest.yaml#uses.tables`, `lambda:InvokeFunction` solo sobre el ARN
  de `send_email` (declarado en `manifest.yaml#uses.invokes: [send_email]`,
  expuesto al runtime via la env var `LAMBDA_SEND_EMAIL_FUNCTION_NAME`) y
  los 4 secretos SSM (`turnstile-secret`, `turnstile-bypass-public-key`,
  `neon-url`, `jwt-secret`). NUNCA wildcard. El `auth` ya NO declara la
  cola SQS auth-email ni `ses-from-address`.
- **SIEMPRE** el Lambda `send_email` (no `auth`) tiene el IAM scoped para
  SES por **identity ARN exacto**
  (`arn:aws:ses:us-east-1:<account-id>:identity/the-full-stack.com`),
  ademas de la tabla `email-config` y el bucket S3 de templates. NUNCA
  `Resource: *` ni `ses:*`.

### MFA + WebAuthn (plan 02)

- **SIEMPRE** el TOTP secret se cifra con `kms:Encrypt` CMK directa
  (`alias/portfolio-lambdas` + `EncryptionContext={user_id,
  purpose:totp}`) antes de persistir en `auth_mfa_methods.
  totp_secret_ciphertext`. NUNCA envelope (sin `GenerateDataKey`, sin
  AES-GCM propio, sin nonce), NUNCA plain, NUNCA loguear el secret ni el
  `secret_b32`. Se importa via `shared.aws.kms_encrypt`/`kms_decrypt`.
- **SIEMPRE** `pyotp` se importa via `shared.auth` (`generate_totp_secret_b32`,
  `verify_totp_code` con `valid_window=1`, `build_otpauth_url`). El QR lo
  renderiza el FRONTEND desde el `otpauth_url` (sin `segno` en el Lambda).
- **SIEMPRE** los recovery codes son 10 codes de 10 chars Crockford-like
  (CSPRNG via `secrets.choice`), hash SHA-256 en `auth_mfa_recovery_codes`,
  mostrados UNA sola vez. Comparacion constant-time
  (`secrets.compare_digest`). NUNCA en plain.
- **SIEMPRE** `recovery-codes-consume` exige un temp JWT
  `flow='login-mfa'` step=2 (factor fuerte: password / webauthn). Un temp
  de magic-link / email-code -> `403 RECOVERY_REQUIRES_STRONG_FACTOR`.
  NUNCA usar un claim `prev` (JwtClaims tiene `extra='forbid'`): el factor
  previo se codifica con el `flow`.
- **SIEMPRE** `python-fido2` se importa via `shared.auth`
  (`build_register_options`, `verify_registration`, `build_login_options`,
  `verify_authentication`, `WebauthnError`/`WebauthnVerifyError`/
  `WebauthnCloneError`). NUNCA `import fido2` en `core/`.
- **SIEMPRE** el WebAuthn challenge vive en DDB
  `portfolio-webauthn-challenges-${stage}` con TTL 5 min, single-use
  (`get_and_consume` borra el row). NUNCA en Neon.
- **SIEMPRE** validar `sign_count` monotonico: si `new <= stored` (con
  `stored > 0`) -> `WebauthnCloneError` -> `401 WEBAUTHN_CLONE_DETECTED`
  + marca el credential `disabled_at=now()` SIEMPRE (clone detection).
- **SIEMPRE** el `public_key` se guarda como CBOR (`fido2.cbor.encode`) en
  `auth_webauthn_credentials.public_key`. UV `PREFERRED` en register,
  `REQUIRED` en login.
- **SIEMPRE** las actions de la operation `mfa` (salvo
  `recovery-codes-consume`) y `webauthn` (salvo `login-options`/
  `login-verify`) requieren access JWT (`require_active_user`).
- **SIEMPRE** al confirmar el PRIMER metodo MFA del user (`total_mfa: 0
  -> 1`, via `mfa.confirm-totp`, `mfa.setup-email-code` o
  `webauthn.register-verify`) se revoca la familia de refresh: setea
  `auth_users.sessions_revoked_at = now()` y `session.refresh` rechaza
  refreshes con `iat` anterior con `401 TOKEN_FAMILY_REVOKED` (AC-27).
- **SIEMPRE** el guard `MUST_KEEP_ONE_MFA_METHOD` es transversal
  (`count_active_mfa` = `auth_mfa_methods` confirmados activos +
  `auth_webauthn_credentials` activos). `disable`/`delete-credential` que
  deje `total_mfa == 0` -> `409`. Credential/metodo de otro user -> `404
  NOT_FOUND` (anti-enumeration).
- **SIEMPRE** el `WEBAUTHN_RP_ID` es por env: apex `the-full-stack.com` en
  prod, `portfolio.dev.the-full-stack.com` en dev,
  `portfolio.stage.the-full-stack.com` en stage. Un passkey NO migra
  entre envs (es esperado).
- **NUNCA** editar la migration `00000003_auth_mfa.py` aplicada; nuevo
  cambio = migration nueva. El `downgrade` NO se corre en prod.

### Gestion de usuarios (plan 03 — Lambda `users`)

- **SIEMPRE** el Lambda `users` sigue lambda-controller (handler delgado
  -> `http_handler` con `cors_origin='echo'`; un controller por action;
  logica en `core/services/`). 3 operations: `profile`, `status`, `admin`.
- **SIEMPRE** el `require_active_user` de `users` (en su `jwt_service.py`)
  devuelve **403 `ACCOUNT_DISABLED`** (no 401) para un user disabled con
  JWT valido, y 403 `ACCOUNT_LOCKED` para locked (AC-16). 401 queda para
  token ausente/invalido/revocado o user soft-deleted/inexistente.
- **SIEMPRE** el scope `admin.*` valida via `shared.auth.require_admin`
  (whitelist SSM `/portfolio/${stage}/admin-emails`). NO-admin -> **404
  NOT_FOUND** (anti-enumeration, NO 403).
- **SIEMPRE** las admin operations escriben `auth_user_admin_actions`
  ANTES de la accion destructiva (audit pre-hoc, inmutable).
- **SIEMPRE** el soft-delete (`profile.delete-account`) es UPDATE de
  `deleted_at` + anonimiza email + DELETE explicito en credentials / mfa /
  recovery / webauthn / email_codes / magic_links / sessions (las FK
  CASCADE NO se disparan en UPDATE) + blacklistea las families.
- **SIEMPRE** el access JWT lleva `family_id` (param opcional de
  `issue_access_jwt`) para que `status.*` identifique la sesion en curso.
- **SIEMPRE** el session tracking del Lambda `auth`
  (`SessionTrackingService`) es best-effort: un fallo de Neon NO rompe
  login/refresh/logout.
- **SIEMPRE** el rate-limit de `users` usa `turnstile_validated=False`
  (endpoints JWT-authed sin Turnstile; True auto-blacklistearia users
  legitimos con 3+ requests/60s).
- **SIEMPRE** el dispatcher de email del Lambda `users` invoca `send_email`
  async con el payload
  `{operation:'email', action:'send', data:{kind, to:[to], data:{**data,
  user_id, niche, subject_id}}}` — con `subject_id`, SIN
  `schema_version`/`locale`. NUNCA publica a SQS.
- **NUNCA** un admin se borra a si mismo via `profile.delete-account` si
  su email esta en la whitelist (`409 CANNOT_DELETE_ADMIN_ACCOUNT`, AC-29).
- **NUNCA** un user revoca su propia sesion via `status.revoke-session`
  (`400 CANNOT_REVOKE_CURRENT_SESSION` -> usar `auth.session.logout`).
- **NUNCA** editar la migration `00000004_auth_users_extension.py`
  aplicada; nuevo cambio = migration nueva. `ALTER TYPE ADD VALUE` corre
  en `autocommit_block`.

### Anti-patrones (correcciones criticas)

| Anti-patron | Correccion |
|---|---|
| `import jwt` en el `core/` de auth | `from shared.auth import issue_temp_jwt, verify_jwt, ...` |
| `import pyotp` / `import fido2` en `core/` | `from shared.auth import verify_totp_code, verify_authentication, ...` |
| `import boto3` para KMS en `core/` | `from shared.aws import kms_encrypt, kms_decrypt` |
| Guardar el TOTP secret en plain o con envelope (DataKey) | `kms:Encrypt` CMK directa + EncryptionContext, BYTEA |
| Recovery code en plain o comparado con `==` | hash SHA-256 + `compare_recovery_code` (constant-time) |
| WebAuthn challenge en Neon | DDB con TTL 5 min, single-use (`get_and_consume`) |
| Ignorar regresion de `sign_count` | clone detection -> disable credential + 401 |
| `recovery-codes-consume` tras magic-link/email-code | exige temp `flow='login-mfa'` step=2 (factor fuerte) |
| RP_ID unico para todos los envs | RP_ID por env (apex prod, `portfolio.{dev,stage}...`) |
| Permitir quedar en `total_mfa == 0` | guard transversal `MUST_KEEP_ONE_MFA_METHOD` |
| `import argon2` o `from passlib import ...` | `from shared.auth import hash_password, verify_password` |
| Comparar codes con `==` (timing attack) | `from shared.auth import compare_code` (secrets.compare_digest) |
| Generar code con `random.choice` | `secrets.choice` via `shared.auth.generate_code` (CSPRNG) |
| Loggear JWT/code/token | log solo `jti`, `user_id`, `event`, NUNCA el valor |
| Email distinto en respuesta a "no existe" vs "disabled" | Mismo 404, solo `suggest_register` cambia |
| Token de magic-link como JWT | Opaco 32 bytes b64url; hash SHA-256 en `auth_magic_links.token_hash` |
| Hardcodear secret en `manifest.yaml` | SSM SecureString + KMS; `@cached_property` en AppConfig |
| Lambda `auth` enviando SES directo | Invocar `send_email` async (`InvocationType='Event'`) |
| Publicar emails de auth a una cola SQS / mantener un worker SQS-consumer | Invoke directo a `send_email` (`{operation:'email', action:'send', data:{...}}`) |
| Reusar `family_id` entre sesiones | Cada login = `family_id` nuevo (uuidv7) |
| Editar migration `00000002` ya aplicada | Migration nueva (forward fix) |
| Rate-limit con prefix matching | Exacto `<operation>.<action>` literal |
| NO-admin -> `403 FORBIDDEN` | `404 NOT_FOUND` (anti-enumeration, AC-11) |
| `require_active_user` 401 para user disabled | 403 `ACCOUNT_DISABLED` (JWT valido, AC-16) |
| soft-delete via `session.delete(user)` esperando cascade | UPDATE `deleted_at` + DELETE explicito por tabla hija |
| Session tracking que rompe el login si Neon falla | best-effort (try/except + log) |
| `turnstile_validated=True` en endpoints de `users` | `False` (auto-blacklist a users legitimos) |
| Dispatcher de `users` con `schema_version`/`locale` | invoke `send_email` con `data:{**data,user_id,niche,subject_id}` (sin `schema_version`/`locale`) |

## Verificacion antes de commit (recordatorio)

```bash
# Tests del subpackage shared.auth
python devtools/run.py serverless tests --type=unit --shared

# Tests del Lambda auth
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth   # >=80% per-file

# Tests del Lambda users (plan 03)
python devtools/run.py serverless tests --type=unit --lambda=users
python devtools/run.py serverless tests --type=coverage --lambda=users   # >=80% per-file

# Lint deps (shared-only imports + dedup D-3)
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless lint-deps --lambda=users
python devtools/run.py serverless lint-deps --shared
```

## Referencias cruzadas

- [.claude/docs/auth-system/README.md](../docs/auth-system/README.md) —
  knowledge tree del dominio
- [.claude/docs/auth-system/01-jwt-lifecycle.md](../docs/auth-system/01-jwt-lifecycle.md)
- [.claude/docs/auth-system/02-flows.md](../docs/auth-system/02-flows.md)
- [.claude/docs/auth-system/03-rate-limit-rules.md](../docs/auth-system/03-rate-limit-rules.md)
- [.claude/docs/auth-system/04-mfa.md](../docs/auth-system/04-mfa.md) —
  TOTP, email-code, recovery codes, login con password, AC-27
- [.claude/docs/auth-system/06-users.md](../docs/auth-system/06-users.md)
  — Lambda `users`: profile + status (plan 03)
- [.claude/docs/auth-system/07-admin.md](../docs/auth-system/07-admin.md)
  — whitelist SSM + admin actions + audit
- [.claude/docs/auth-system/08-sessions.md](../docs/auth-system/08-sessions.md)
  — sessions tracking (`auth_user_sessions`, family_id en access JWT)
- [.claude/docs/auth-system/05-webauthn.md](../docs/auth-system/05-webauthn.md)
  — passkeys, RP_ID por env, clone detection, challenges DDB
- [.claude/rules/lambda-controller.md](lambda-controller.md) — patron
  general
- [.claude/rules/lambda-shared-imports.md](lambda-shared-imports.md) —
  catalogo de portadores
- [.claude/rules/neon-management.md](neon-management.md) — operacion de
  Neon (migrations via la Lambda `db`, branches)
- [.claude/rules/serverless-secrets.md](serverless-secrets.md) — SSM +
  KMS + IAM scopes
- Skill: `/auth-system`
