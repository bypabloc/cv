# 07. Admin — whitelist + admin actions + audit

> [README](README.md) · anterior: [06-users](06-users.md) ·
> siguiente: [08-sessions](08-sessions.md)

La operation `admin.*` del Lambda `users` (plan 03) es el panel de
administracion: scope restringido a una whitelist de emails leida de SSM
(solo Pablo hoy). 7 actions.

## Authz por whitelist SSM

- SSM `/portfolio/${stage}/admin-emails` (SecureString + KMS), lista
  coma-separada. Rotar admins = editar el SSM (sin tocar codigo ni DB —
  decision 2 del plan).
- `shared.auth.admin`: `load_admin_emails()` (cache TTL 5 min),
  `is_admin(email)`, `require_admin(email)` (levanta `AdminAuthzError`,
  status 404, code `NOT_FOUND`).
- `services/users/core/services/admin_service.require_admin_user(user,
  *, ip, user_agent, audit_action)`: valida `is_admin(user.email)`; si NO
  es admin, registra el intento fallido en `auth_user_admin_actions` y
  re-levanta `AdminAuthzError`.
- **AC-11 (anti-enumeration)**: un NO-admin recibe `404 NOT_FOUND`, NO
  `403` — oculta la existencia del scope admin.

## Actions

| Action | Efecto | Status |
|--------|--------|--------|
| `list-users` | paginado cursor-based (uuidv7 id ASC); `{users, next_cursor, page_size, total_returned}` | 200 |
| `get-user` | detalle: profile + MFA summary + sessions_count + recent_audit (top 10). NUNCA password/TOTP. Si soft-deleted: row con `deleted_at` + email anonimizado (AC-28) | 200 / 404 |
| `disable-user` | UPDATE status=disabled + audit + notifica al user (kind `account-disabled`). `CANNOT_DISABLE_SELF` si target == actor | 204 / 400 / 404 |
| `enable-user` | UPDATE status=active + audit (idempotente) | 204 / 404 |
| `force-logout` | borra TODAS las sesiones del target + blacklistea cada family + audit (NO cambia el status) | 204 / 404 |
| `delete-user` | hard-delete con cascada; sentinel `HARD-DELETE-USER-<user_id>` obligatorio; `auth_audit_log` queda con user_id SET NULL; `CANNOT_DELETE_SELF` | 204 / 400 / 404 |
| `list-admin-actions` | historico paginado, filtrable por from_date/to_date | 200 |

## Audit inmutable (`auth_user_admin_actions`)

- Cada admin operation destructiva (disable/enable/force-logout/delete)
  inserta un row ANTES de la accion (audit pre-hoc):
  `{admin_user_id, target_user_id, action, metadata, ip, user_agent,
  created_at}`.
- FK `admin_user_id` + `target_user_id` con `ON DELETE SET NULL`: si el
  user borrado fue admin o target, el audit se conserva con la referencia
  en NULL (compliance, sin PII personal).
- `delete-user`: el audit row se inserta con `target_user_id=target.id`;
  el hard-delete posterior lo deja en NULL via la FK SET NULL.
- Los intentos de acceso admin FALLIDOS tambien se registran
  (`require_admin_user` con `success=false`) — defensa contra probing.

## Interaccion con `auth.login.start`

`admin.disable-user` setea `auth_users.status=disabled`. El siguiente
`auth.login.start` de ese user devuelve `403 ACCOUNT_DISABLED` (logica del
plan 01). Para invalidacion inmediata de sesiones vivas, usar tambien
`admin.force-logout` (el `disable` por si solo NO mata el access JWT vivo;
`require_active_user` de `users` SI lo rechaza con 403 en el proximo
request — AC-16).

## Reglas duras

- **SIEMPRE** `require_admin` valida via SSM (no hardcodear el email).
- **SIEMPRE** `admin.*` escribe `auth_user_admin_actions` ANTES de la
  accion destructiva.
- **SIEMPRE** NO-admin -> `404 NOT_FOUND` (no 403).
- **NUNCA** un admin ve password_hash / TOTP secret / recovery hashes de
  otro user (solo metadata).

[↑ README](README.md)
