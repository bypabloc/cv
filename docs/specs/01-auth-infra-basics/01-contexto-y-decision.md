# 01. Contexto y decision

## 1. Contexto / Problema

El portfolio (the-full-stack.com) hoy no tiene ningun mecanismo de
autenticacion. El backend serverless cubre 4 dominios (`cv`, `contact_form`,
`tracking_pixel`, `db` migration runner) + 2 workers async, todos
publicos y sin usuario. Para habilitar:

- Pago / dashboard de admin / area privada
- Comentarios moderados o reactions en proyectos
- API endpoints para terceros con scope/token
- Multi-device session management (futuro)

…hace falta un sistema de autenticacion completo: registro, login con
multiples mecanismos (magic link, codigo al email, contrasena, MFA,
passkeys), gestion de sesion via JWT con blacklist real (logout
invalida el token) y un dominio relacional de usuarios.

Este es el **plan 1 de 3**. Entrega los flujos basicos
(register/login/verify/logout) y la infraestructura comun (schema Neon,
shared subpackage, DynamoDB para blacklist + codes, cola SQS + worker
de email). El plan 2 agrega MFA (TOTP + email-code + WebAuthn). El
plan 3 agrega el Lambda `users` con CRUD de perfil y status.

### Hallazgos de exploracion

- El repo ya tiene la infraestructura compartida lista para reusar:
  `shared.lambda_kit.http_handler` (con `cors_origin='echo'|'public'`,
  `success_status`, `metric_names`), `shared.http.verify_turnstile_token`,
  `shared.aws.send_email` (SES v2 helper), `shared.aws.get_secret_by_name`
  (SSM con cache + KMS decrypt), `shared.rate_limit.check_or_raise`,
  `shared.cache.cached`, `shared.db` (SQLAlchemy + Alembic con
  `run_migrate`/`run_downgrade`).
- El patron de cola SQS + worker async ya esta probado:
  `contact_form` publica a `portfolio-contact-form-${stage}`, el
  `contact_worker` la consume y envia via SES. Repetimos para `auth`.
- El schema Neon usa prefijos por dominio (`cv_`, `vis_`, `tax_`,
  `i18n_`). Agregamos `auth_*` como dominio nuevo.
- No hay deps de auth declaradas en ningun pyproject de shared: hay
  que agregar `pyjwt` + `argon2-cffi` desde cero. Para mantener el
  contrato "un paquete externo = un shared portador", creamos el nuevo
  subpackage `shared.auth`.
- El SSM tiene KMS key `alias/portfolio-lambdas` y patron de paths
  `/portfolio/${stage}/<nombre>`. Sumamos `/portfolio/${stage}/jwt-secret`.
- `cv_profiles.email` ya existe (varchar). Sera el unico row con
  `auth_users.profile_id` no nulo, manual.

## 2. Solucion Propuesta

Lambda `auth` HTTP POST `/auth` con `http_handler` del repo: el cliente
envia `{operation, action, data, _meta}`. 5 operations:
`register`, `login`, `verify`, `session`, y un futuro `mfa`/`webauthn`
(plan 2).

Estado:

- **Relacional en Neon** (`auth_*`): tabla `auth_users` (id, email
  CITEXT UK, status enum, profile_id FK nullable a cv_profiles,
  timestamps), `auth_credentials` (user_id PK, password_hash nullable,
  password_set_at, last_password_change), `auth_email_codes` (id, user_id
  FK, code_hash, kind enum, attempts, expires_at, consumed_at),
  `auth_magic_links` (id, user_id FK, token_hash, kind enum, expires_at,
  consumed_at), `auth_audit_log` (id, user_id FK NULL, event, ip,
  user_agent, niche, success bool, error_code, created_at).
- **DynamoDB con TTL**:
  - `portfolio-jwt-blacklist-${stage}`: PK `jti`, columnas
    `revoked_at`, `reason`, `user_id`, TTL `exp`. Cubre temp + access +
    refresh.
  - `portfolio-auth-codes-${stage}`: PK `pk` (formato
    `<kind>#<user_id>` p. ej. `register#01H...`), columnas
    `code_hash`, `attempts`, `created_at`, TTL `expires_at`. Espejo
    rapido del row de Neon para chequeo O(1) sin tocar Neon en cada
    intento. (Se inserta en paralelo; la fuente de verdad es Neon.)

> Nota: mantenemos los 2 stores (Neon + DynamoDB) deliberadamente. Neon
> guarda la auditoria + multi-device + queries relacionales; DynamoDB
> da lookup O(1) en cada request HTTP sin pagar latencia de Neon.

- **JWT HS256** firmado con secret leido de SSM en cold start de cada
  Lambda. 3 tipos:
  - `typ=temp` (TTL 5 min, rolling). Claim extra `flow`
    (`register`|`login`|`set-password`|`set-mfa`) y `step` (numerico).
    Cada API del flujo blacklistea el `jti` recibido y emite uno nuevo.
  - `typ=access` (TTL 15 min). Stateless. Verificacion = signature +
    `exp` + blacklist lookup (DynamoDB GetItem por `jti`).
  - `typ=refresh` (TTL 30 dias). Rotacion en cada uso: usar un refresh
    consume su row de blacklist y emite uno nuevo. El claim `family_id`
    detecta reuso (si llega un refresh ya consumido, se revoca toda la
    familia — token theft detection).

- **Cola SQS** `portfolio-auth-email-${stage}` (visibility 180s, MRT
  4 dias, redrive a DLQ con `max_receive_count: 3`). El Lambda `auth`
  publica `{kind, to, subject_id, data}` y el worker
  `auth_email_worker` lo consume, renderiza la plantilla y manda con
  `send_email(...)`.

### Decisiones clave

**Decision 1: shared subpackage nuevo `shared.auth`** — los paquetes
externos `pyjwt`, `argon2-cffi`, `secrets` (stdlib pero documentado)
necesitan portador segun la regla `lambda-shared-imports`. Se podria
poner en `shared.core`, pero `core` ya carga 2 paquetes externos
(pydantic, pydantic-settings). Crear `shared.auth` mantiene un dominio
por subpackage. Internal-deps de `shared.auth`: `core` (para
`new_uuidv7`, `Settings`), `aws` (para `get_secret_by_name` del
JWT_SECRET), `observability` (logger).

**Decision 2: token de magic-link es opaco, NO JWT** — un magic-link
es un secret de proposito unico, 32 bytes random b64url-encoded.
Guarda hash (SHA-256) en Neon `auth_magic_links.token_hash`. Verifica
con `secrets.compare_digest(hash(received_token), stored_hash)`. NO
firmamos el token para evitar que un atacante con el JWT secret pueda
generar magic-links arbitrarios.

**Decision 3: codigo de 8 chars con alfabeto Crockford-like sin
confundibles** — alfabeto `'ABCDEFGHJKMNPQRSTUVWXYZ23456789'` (sin
`O/0/I/1/L`). 30 chars, 8 posiciones = `30^8 ~ 6.5x10^11` espacio. Con
5 intentos max, prob. de adivinar < `5 / 6.5x10^11 < 10^-11`. Bajo
rate-limit estricto (5 intentos / 15 min), brute force inviable.
Generador: `secrets.choice(ALPHABET)` (CSPRNG, no `random.choice`).

**Decision 4: rolling temp JWT con blacklist + emision nueva** — cada
API del flujo: (1) valida temp JWT (signature + exp + NOT in blacklist),
(2) ejecuta el step, (3) blacklistea el `jti` viejo en
`jwt-blacklist` con TTL = exp original, (4) emite un temp JWT NUEVO
con `now+5min` y lo devuelve en el body. Frontend sustituye en cada
response. Si el user esta inactivo 5 min, el JWT expira por `exp`. Si
intenta replay (reusar el viejo), falla por blacklist.

**Decision 5: login.start con email no-existente devuelve 404 +
sugerencia** — el usuario pidio explicitamente esta UX. Tradeoff
aceptado: permite user enumeration. Mitigaciones: Turnstile
obligatorio en `login.start`, rate-limit 5/min/IP, no se devuelve
detalle del status del user (solo "no existe" o "existe + metodos").

**Decision 6: response final del flujo (post-validacion exitosa)** —
devuelve `{access_token, refresh_token, expires_in, token_type:
'Bearer', user: {id, email, status}}`. Los tokens vienen en el body
para que el frontend los persista (localStorage / IndexedDB). NO
usamos cookies HttpOnly aqui — el portfolio es API-first y los 6
niches deben poder consumirlo desde cualquier subdominio.

**Decision 7: status del usuario** — enum
`pending|active|disabled|locked|deleted`:
- `pending`: registro iniciado pero magic-link/code aun no verificado.
- `active`: validado y operativo.
- `disabled`: deshabilitado por admin (plan 3).
- `locked`: bloqueo automatico tras 10 fallos consecutivos en 5 min.
- `deleted`: soft-delete (no aplica en plan 1, futuro plan 3).

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given un POST `/auth` con `{operation: 'register', action: 'start',
  data: {email: 'nuevo@x.com', cf_turnstile_response: 'valid'}}`,
  When el email no existe y Turnstile valida, Then el endpoint:
  (a) crea row `auth_users` con status=`pending`,
  (b) genera magic-link + code de 8 chars,
  (c) publica 1 mensaje SQS para email magic-link + 1 para email code,
  (d) devuelve `201 {temp_token, user_id, expires_in: 300}`.

- **AC-2**: Given `register.start` con email ya `active` y mismo Turnstile,
  When se procesa, Then devuelve `409 {error: 'EMAIL_ALREADY_REGISTERED'}`
  y registra fila en `auth_audit_log` con event=`register.start.duplicate`.

- **AC-3**: Given el magic-link recibido por email (URL
  `/auth?operation=register&action=verify-magic-link&token=<X>`),
  When el user lo clickea (GET), Then el endpoint:
  (a) verifica `token_hash` en Neon,
  (b) actualiza `auth_users.status='active'`,
  (c) marca `auth_magic_links.consumed_at=now()`,
  (d) emite access + refresh JWT,
  (e) devuelve un HTML 200 con auto-redirect + `localStorage.setItem`
    de los tokens y redirect al hub (`hub.portfolio.{env}.the-full-stack.com`).

- **AC-4**: Given POST `register.verify-code` con `{code, temp_token}`,
  When el code matchea (hash + not expired + attempts<5), Then mismo
  resultado que magic-link verify pero como JSON `200 {access_token,
  refresh_token, expires_in, user}`.

- **AC-5**: Given POST `login.start` con email NO existente y Turnstile
  valido, Then devuelve `404 {error: 'EMAIL_NOT_FOUND', suggest_register:
  true}`.

- **AC-6**: Given POST `login.start` con email `active` sin password ni
  MFA configurados, Then devuelve `200 {temp_token, methods: ['magic-link',
  'email-code'], expires_in: 300}` y envia magic-link + code.

- **AC-7**: Given POST `session.refresh` con un refresh JWT valido,
  Then: (a) blacklistea el refresh viejo, (b) emite access + refresh
  nuevos, (c) devuelve `200 {access_token, refresh_token, expires_in}`.

- **AC-8**: Given POST `session.refresh` con un refresh JWT ya
  consumido (reuso detectado), Then: (a) revoca toda la familia
  (`family_id` -> todos los refresh JWT activos), (b) devuelve
  `401 {error: 'TOKEN_REUSE_DETECTED'}`, (c) registra evento
  `session.refresh.reuse_detected` en audit log.

- **AC-9**: Given POST `session.logout` con access JWT, Then: (a)
  blacklistea ese `jti`, (b) blacklistea el refresh JWT
  asociado (via `family_id`), (c) devuelve `204`.

- **AC-10**: Given una request a cualquier endpoint del flujo con JWT
  temp ya blacklisteado (rolling refresh detecta replay), Then devuelve
  `401 {error: 'TOKEN_BLACKLISTED'}`.

- **AC-11**: Given >5 intentos fallidos en `verify-code` (cualquier
  variante) en 5 min para el mismo user, Then `auth_users.status='locked'`
  y proximas requests devuelven `423 {error: 'ACCOUNT_LOCKED',
  unlock_at: <ts+1h>}`.

- **AC-12**: Given una request a `register.start` o `login.start` sin
  `cf_turnstile_response` o con token invalido, Then devuelve
  `403 {error: 'TURNSTILE_FAILED'}` ANTES de tocar Neon o SQS.

- **AC-13**: Given el rate-limit excedido (ej. 6ta request a
  `login.start` desde misma IP en 60s), Then devuelve `429 {error:
  'RATE_LIMITED', retry_after: <segs>}`.

- **AC-14**: Given el Lambda `auth_email_worker` recibe un mensaje
  SQS con `{kind: 'register-magic-link', to: 'x@y.com', user_id,
  token, niche}`, Then: (a) renderiza la plantilla, (b) llama
  `send_email(from=ses_from_address, to=[to], subject=..., text=...,
  html=...)`, (c) registra `auth_audit_log` event=`email.sent.magic-link`.

- **AC-15**: Given la migration `00000002_auth_schema.py` aplicada en
  un branch Neon de prueba, When se ejecuta `downgrade -1` y luego
  `upgrade head`, Then el schema vuelve al estado original y vuelve a
  crear las 5 tablas `auth_*` sin errores.
