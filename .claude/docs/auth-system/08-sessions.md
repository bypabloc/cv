# 08. Sessions tracking — `auth_user_sessions`

> [README](README.md) · anterior: [07-admin](07-admin.md)

Tracking de sesiones activas multi-device (plan 03). La tabla
`auth_user_sessions` (Neon) la **escribe el Lambda `auth`** (via
`SessionTrackingService`) y la **lee/revoca el Lambda `users`**
(`status.list-sessions`, `status.revoke-session`, `admin.force-logout`).

## Modelo

`auth_user_sessions`: `{id, user_id (FK CASCADE), family_id (UNIQUE),
device_info (jsonb), ip, country, user_agent, created_at,
last_active_at}`. 1 row por familia de refresh (cada login = nueva
familia uuidv7).

## El access JWT lleva `family_id` (plan 03)

Para que `users` identifique la sesion EN CURSO (marcar `current`,
bloquear revocar la actual — AC-8/AC-10), el access JWT ahora embebe el
`family_id` de su sesion. `shared.auth.issue_access_jwt` gana un parametro
`family_id` opcional (backward-compatible: si es None, el claim no se
incluye). El Lambda `auth` lo pasa en cada emision terminal. El Lambda
`users` lo lee con `authenticate()` -> `claims.family_id`.

## SessionTrackingService (en el Lambda `auth`)

`services/auth/core/services/session_tracking_service.py`. **Todas las
escrituras son best-effort** (try/except que traga la excepcion + log): un
fallo de Neon NO rompe login/refresh/logout. El tracking es metadata, no
camino critico.

- `on_session_created(user_id, family_id, ip, country, user_agent)`:
  INSERT. `device_info` se deriva del user-agent (`_parse_device_info`:
  browser/os/device_type, heuristica regex sin deps).
- `on_session_rotated(old_family_id, new_family_id)`: el refresh REUSA el
  mismo family_id (rotation), asi que es un bump de `last_active_at`.
- `on_session_revoked(family_id)`: DELETE el row de esa family (logout).

## Puntos de inyeccion en el Lambda `auth`

| Controller | Hook |
|------------|------|
| register/verify_code, register/verify_magic_link | on_session_created |
| login/verify_code, login/verify_magic_link | on_session_created |
| login/_mfa_login.issue_terminal_tokens (cubre login/start, login/verify_password no-MFA, login/verify_totp) | on_session_created |
| webauthn/login_verify | on_session_created |
| mfa/recovery_codes_consume | on_session_created |
| session/refresh | on_session_rotated (mismo family) |
| session/logout | on_session_revoked (si llega refresh) |

En cada create-site el `family_id` se genera ANTES de emitir el access
(para embeberlo en sus claims) y luego se llama al tracking.

## Sesiones pre-deploy quedan invisibles

Refresh tokens emitidos ANTES del deploy de `auth` con tracking NO tienen
row en `auth_user_sessions`. `status.list-sessions` los muestra vacios
hasta que el user haga `session.refresh` (bump) o re-login. Es esperado,
no un bug.

## Revocacion

- `status.revoke-session`: borra el row (dual filter user_id) +
  blacklistea su family en DDB (`jwt_svc.revoke_families` con TTL 30d).
  No permite la sesion actual (AC-10).
- `admin.force-logout` / `profile.delete-account`: borra TODAS las
  sesiones del user + blacklistea cada family.

## AC cubiertas

AC-8 (list con current), AC-9 (revoke), AC-10 (no revocar actual),
AC-22 (create on login), AC-23 (rotate on refresh), AC-24 (delete on
logout).

[↑ README](README.md)
