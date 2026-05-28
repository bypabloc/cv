# 01. Contexto y decision

## 1. Contexto / Problema

Tras planes 01 + 02 el portfolio tiene:

- Schema Neon `auth_users`, `auth_credentials`, `auth_email_codes`,
  `auth_magic_links`, `auth_audit_log`, `auth_mfa_methods`,
  `auth_mfa_recovery_codes`, `auth_webauthn_credentials`.
- Lambda `auth` con 5 operations (`register`, `login`, `verify`,
  `session`, `mfa`, `webauthn`).
- Cola SQS + worker `auth_email_worker` con 5 plantillas.

El usuario en la peticion original pidio explicitamente **2
Lambdas**: `auth` (autenticacion) + un segundo Lambda para **gestion
de usuarios**: "creacion, status, login, logout, register". Los planes
01 + 02 entregaron toda la parte de autenticacion (creacion via
register, login/logout via session) en el Lambda `auth`. El Lambda
restante, `users`, cubre el **CRUD del perfil + status + admin**.

Sin este plan:

- Un user activo NO puede actualizar su display_name, locale,
  marketing_consent.
- NO hay endpoint admin para Pablo: list/disable/delete users.
- NO hay tracking de sesiones activas (multi-device) — el plan 01 da
  refresh_token con `family_id` pero no expone una API para verlos.
- NO hay self-service delete-account (GDPR).

Este plan completa el inventario solicitado.

### Hallazgos de exploracion

- El patron lambda-controller del repo permite agregar un Lambda
  nuevo en la misma API Gateway sin tocar otros Lambdas. `change_detector.py`
  lo recoge automaticamente.
- El `auth_users.profile_id` FK a `cv_profiles` del plan 01 queda
  intacto; este plan no lo modifica. Solo agrega columnas de
  preferencias.
- El `auth_audit_log` del plan 01 ya soporta cualquier event string;
  podemos agregar `users.*` events sin migration.
- SSM con `SecureString` + KMS para la lista de admin-emails es el
  mismo patron que `jwt-secret`.
- `auth_email_worker` puede agregar plantillas sin redeploy del
  lambda `auth` (los kinds son strings que llegan en el mensaje SQS).

## 2. Solucion Propuesta

Lambda `users` nuevo, HTTP POST `/users`. Codigo siguiendo el mismo
formato que `auth` (handler delgado, http_handler, controllers, services).

3 operations:

- `profile`: CRUD del perfil del propio user (self).
- `status`: visibilidad del estado + sesiones activas.
- `admin`: scope para Pablo (whitelist por SSM).

Schema delta:
- Agregar columnas a `auth_users`: `display_name`, `locale`, `timezone`,
  `marketing_consent`, `privacy_policy_version`, `deleted_at`.
- Agregar enum `email-change` al type `auth_link_kind` existente
  (reuso de `auth_magic_links` table para change-email flow).
- Nuevas tablas: `auth_user_sessions`, `auth_user_admin_actions`,
  `auth_user_consent_log`.

Cero cambio en el Lambda `auth`. Solo el schema y un nuevo Lambda.

### Decisiones clave

**Decision 1: Lambda `users` separado** — confirmado en el dialogo
original. Beneficios: aislamiento de dominios, IAM least privilege
(users NO necesita KMS para TOTP), deploy independiente, separation
of concerns. Costo: 1 lambda extra (gratis en AWS free tier hasta 1M
invocaciones/mes).

**Decision 2: admin via SSM whitelist** — `/portfolio/${stage}/admin-emails`
como `SecureString` (lista coma-separada). Lambda `users` lee en cold
start con TTL 5 min. Para rotar admin: editar SSM. NO se cambia codigo.

Alternativa rechazada: columna `auth_users.role` enum. Mas
"correcto" pero requiere migration por cada cambio de rol. Para un
portfolio con 1 admin (Pablo) la whitelist es overkill suficiente.

Cuando aplique (futuro), si hay >5 admins, migrar a tabla
`auth_user_roles` con FK.

**Decision 3: sesiones tracking via `auth_user_sessions`** —
cuando el lambda `auth` emite refresh_token, INSERT en
`auth_user_sessions` con `family_id`, `device_info` (extraido de
user_agent: browser + os), `ip`, `created_at`, `last_active_at`. Cada
refresh: UPDATE `last_active_at`. Logout: DELETE row. Force-logout
admin: DELETE row + blacklist family.

Implica modificacion al lambda `auth`: tras `session.refresh` y
`register.verify-magic-link` / `login.verify-*`, INSERT (o UPDATE) en
esta tabla. **Riesgo**: agrega complejidad al lambda `auth` despues de
estar "cerrado". Mitigacion: este plan toca SOLO los archivos de
`services/sessions_persistence.py` (nuevo helper) e inyecta su
llamada en 4 puntos especificos del lambda `auth`. Cambios minimos,
test cobertura adicional.

**Decision 4: change-email reusa `auth_magic_links`** — agregar
`email-change` al enum `auth_link_kind`. La migration de plan 01
debe permitir ALTER TYPE para agregar valores. Migration 00000004
incluye:

```sql
ALTER TYPE auth_link_kind ADD VALUE IF NOT EXISTS 'email-change';
```

(PostgreSQL 18 soporta esto sin recrear el tipo.)

**Decision 5: soft-delete del user con re-uso de email** — `auth_users`
tiene constraint `UNIQUE(email) WHERE deleted_at IS NULL` (partial
index). Esto permite que un email se libere al soft-delete y se pueda
re-registrar. Caso edge: si un atacante registra el email de un user
deleted, hay anonymity break — mitigacion: el flow de re-register
trata al email como inexistente (mantiene la consistencia).

**Decision 6: paginacion cursor-based para list-users** — usar UUIDv7
del `auth_users.id` (cronologico nativo). Cursor opaco `last_id`
opcional en request; backend hace `WHERE id > last_id ORDER BY id ASC
LIMIT page_size`. Para portfolios con <1k users es overkill pero
escalable.

**Decision 7: hard-delete cascade preservando audit** — `admin.delete-user`
elimina las filas relacionadas en `auth_credentials`,
`auth_mfa_methods`, `auth_mfa_recovery_codes`,
`auth_webauthn_credentials`, `auth_email_codes`, `auth_magic_links`,
`auth_user_sessions`. NO borra `auth_audit_log` (FK SET NULL en
`user_id`). Preserva `auth_user_admin_actions` rows como audit
admin con `target_user_id` reference (eventualmente NULL si target
borrado).

## 3. Criterios de Aceptacion

### Profile

- **AC-1**: Given user activo con access JWT, When llama
  `POST /users operation=profile action=get`, Then devuelve `{id, email,
  display_name, locale, timezone, marketing_consent, status, created_at,
  email_verified_at, mfa_configured: bool}`. NO devuelve password_hash,
  TOTP secret ni info sensible.

- **AC-2**: Given user activo, When llama `profile.update` con
  `{display_name, locale, timezone, marketing_consent}`, Then UPDATE
  los campos enviados (parcial) y devuelve el row actualizado.

- **AC-3**: Given user activo cambia `marketing_consent` de false a
  true, Then ademas de UPDATE en `auth_users`, INSERT en
  `auth_user_consent_log(user_id, field='marketing_consent', old_value=false,
  new_value=true, ip, user_agent, created_at)`.

- **AC-4**: Given user activo llama `profile.change-email` con
  `{new_email, password?}`, When new_email NO esta en uso, Then:
  (a) si user tiene password seteada, valida con argon2;
  (b) genera magic-link `auth_magic_links` kind=`email-change` con
      `user_id` actual + nuevo email en metadata,
  (c) publica mensaje SQS para enviar magic-link al `new_email`,
  (d) devuelve `200 {request_id, expires_in: 900}`.

- **AC-5**: Given el magic-link `email-change` clickeado, When es
  valido y no expirado, Then UPDATE `auth_users.email = new_email`,
  marca link consumed, audit log `profile.change-email.confirmed`.

- **AC-6**: Given user activo, When llama `profile.delete-account`
  con `{confirm: 'DELETE-MY-ACCOUNT'}` (sentinel string), Then:
  (a) anonimiza `email = 'deleted-<id>@invalid.local'`,
  (b) marca `deleted_at=now()`,
  (c) borra `auth_credentials`, `auth_mfa_methods`,
      `auth_mfa_recovery_codes`, `auth_webauthn_credentials`,
      `auth_email_codes`, `auth_magic_links` con DELETE explicitos
      dentro de la misma transaccion del UPDATE (NO via FK cascade
      — el UPDATE de `deleted_at` no dispara la cascade),
  (d) blacklistea TODOS los JWT activos del user
      (DELETE `auth_user_sessions` + INSERT en `jwt-blacklist` DDB),
  (e) devuelve `204`.

### Status

- **AC-7**: Given user activo, When llama `status.get`, Then devuelve
  `{status, mfa_configured: bool, mfa_methods: [...], webauthn_count: int,
  recovery_codes_remaining: int, failed_attempts: int, locked_until:
  iso8601|null}`.

- **AC-8**: Given user activo con N sesiones activas, When llama
  `status.list-sessions`, Then devuelve
  `[{session_id, device_info, ip, country, created_at, last_active_at,
  current: bool}, ...]` ordenado por last_active_at DESC. `current:true`
  para la session del access JWT en curso.

- **AC-9**: Given user activo con session_id != current, When llama
  `status.revoke-session` con `{session_id}`, Then DELETE row +
  blacklistea la family completa + devuelve 204.

- **AC-10**: Given user intenta `status.revoke-session` con su
  session_id actual, Then devuelve `400 CANNOT_REVOKE_CURRENT_SESSION`
  (debe usar `auth.session.logout`).

### Admin

- **AC-11**: Given un NO-admin con access JWT, When llama
  `admin.list-users`, Then devuelve `404 NOT_FOUND` (NO 403, evita
  enumeration).

- **AC-12**: Given admin (email en whitelist SSM) con access JWT,
  When llama `admin.list-users` (sin params), Then devuelve los
  primeros 50 users ordenados por created_at DESC + cursor `next`.

- **AC-13**: Given admin, When llama `admin.list-users` con
  `{page_size: 20, cursor: '<last_id_uuid_str>'}`, Then devuelve
  exactamente esta forma:

  ```jsonc
  {
    "users": [ {"id": "...", "email": "...", "status": "active",
                "created_at": "...", "display_name": "..."}, ... ],
    "next_cursor": "<uuid_str>|null",  // null si no hay mas paginas
    "page_size": 20,
    "total_returned": 20               // count exacto de items en `users`
  }
  ```

  Backend filtra `WHERE id > cursor ORDER BY id ASC LIMIT page_size`.
  `next_cursor = users[-1].id` si `total_returned == page_size`, sino
  `null`. Si el cliente pasa un `cursor` no decodificable (no es UUID
  valido), 400 `INVALID_CURSOR`.

- **AC-14**: Given admin, When llama `admin.get-user` con
  `{user_id}`, Then devuelve detalle: profile + status + sessions
  count + audit log mas reciente (top 10). NO password hash, NO TOTP
  secret.

- **AC-15**: Given admin, When llama `admin.disable-user` con
  `{user_id, reason}`, Then UPDATE `auth_users.status='disabled'` +
  INSERT `auth_user_admin_actions(admin_user_id, target_user_id,
  action='disable', metadata={reason}, ip, created_at)` + devuelve 204.

- **AC-16**: Given user disabled, When intenta `auth.login.start`,
  Then `auth.login.start` (logica del plan 01) devuelve HTTP `403`
  con `{error: 'ACCOUNT_DISABLED'}`. Si en cambio tiene un access
  JWT vivo de antes del disable y llama `/users` o `auth.session.*`,
  `require_active_user` tambien devuelve `403 ACCOUNT_DISABLED` (no
  401 — el JWT es valido pero el user esta bloqueado). 401 queda
  reservado para token invalido/ausente. (Re-validacion del
  comportamiento del plan 01, con el nuevo path.)

- **AC-17**: Given admin, When llama `admin.enable-user` con
  `{user_id}`, Then UPDATE `auth_users.status='active'`, audit row,
  devuelve 204.

- **AC-18**: Given admin, When llama `admin.force-logout` con
  `{user_id, reason?}`, Then: DELETE todas las `auth_user_sessions`
  del target + blacklistea TODAS las families activas + audit row +
  devuelve 204.

- **AC-19**: Given admin, When llama `admin.delete-user` con
  `{user_id, confirm: 'HARD-DELETE-USER-<user_id>'}` (sentinel
  obligatorio), Then borra TODAS las filas del target en cascada
  (mantiene `auth_audit_log` con `user_id` SET NULL), audit row
  `admin.delete-user`, devuelve 204.

- **AC-20**: Given admin, When llama `admin.list-admin-actions` con
  `{from_date, to_date}`, Then devuelve historico paginado de las
  admin actions (incluyendo metadata, IP, admin_user_id, target_user_id).

- **AC-21**: Given admin sin sus emails en SSM (admin-emails vacio o
  no contiene el suyo), When llama cualquier `admin.*`, Then 404
  NOT_FOUND (whitelist vacia = sin admins).

### Sessions tracking (integracion con auth)

- **AC-22**: Given un user completa `register.verify-magic-link` o
  `login.verify-*` exitosa, Then el lambda `auth` (via nuevo helper)
  INSERT `auth_user_sessions(user_id, family_id, device_info, ip,
  user_agent, country, created_at, last_active_at)`.

- **AC-23**: Given un user usa `session.refresh`, Then el lambda
  `auth` UPDATE `auth_user_sessions.last_active_at = now()` y
  `family_id = <nuevo>` (rotation). El row se mantiene; cambia el
  family_id.

- **AC-24**: Given un user usa `session.logout`, Then DELETE el row
  de `auth_user_sessions` con el family_id correspondiente.

### Migration

- **AC-25**: Given la migration `00000004_auth_users_extension.py`
  aplicada en branch Neon de prueba, When se ejecuta `downgrade -1` y
  luego `upgrade head`, Then schema vuelve al de plan 02 y se recrean
  las columnas + tablas sin error.

### Seguridad / GDPR

- **AC-26**: Given un user es soft-deleted, When intenta `auth.login.start`
  con su email original, Then devuelve `404 EMAIL_NOT_FOUND` (se
  comporta como inexistente).

- **AC-27**: Given un email previamente soft-deleted, When otro user
  intenta `auth.register.start` con el mismo email, Then exitoso (el
  email esta libre por el partial unique index).

- **AC-28**: Given un user soft-deleted, When admin llama
  `admin.get-user`, Then devuelve el row con `deleted_at` poblado +
  email anonimizado (`deleted-<id>@invalid.local`).

- **AC-29**: Given un user activo cuyo `email` esta en
  `/portfolio/${stage}/admin-emails` SSM (es admin), When intenta
  `profile.delete-account`, Then devuelve `409
  CANNOT_DELETE_ADMIN_ACCOUNT` con mensaje pidiendo que el email se
  remueva de la whitelist antes (defensa contra "ultimo admin se
  borra a si mismo").
