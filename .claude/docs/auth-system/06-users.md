# 06. Lambda `users` — profile + status

> [README](README.md) · anterior: [05-webauthn](05-webauthn.md) ·
> siguiente: [07-admin](07-admin.md)

El Lambda `users` (HTTP `POST /users`, plan 03) gestiona el identity del
propio usuario: CRUD del perfil, estado de la cuenta y sesiones activas.
Separa la gestion del usuario del ciclo de autenticacion (`auth`). Mismo
patron lambda-controller + `http_handler`. Requiere access JWT en todas
las actions salvo `profile.confirm-email-change` (token-based).

## Operations + actions

```text
profile:
  get                 -> perfil del propio user (AC-1)
  update              -> display_name/locale/timezone/marketing_consent (AC-2/3)
  change-email        -> inicia magic-link al email NUEVO (AC-4)
  confirm-email-change-> PUBLICO: confirma el cambio via token (AC-5)
  delete-account      -> soft-delete self-service GDPR (AC-6, AC-29)
status:
  get                 -> status + MFA info (AC-7)
  list-sessions       -> sesiones activas, current marcado (AC-8)
  revoke-session      -> cierra una sesion (no la actual) (AC-9/AC-10)
admin:                  (ver 07-admin.md)
```

## Profile

- **get**: devuelve `{id, email, display_name, locale, timezone,
  marketing_consent, status, created_at, email_verified_at,
  mfa_configured}`. NUNCA password_hash ni TOTP secret.
- **update**: parcial (solo los campos enviados no-None). Si
  `marketing_consent` cambia de valor -> INSERT en
  `auth_user_consent_log` (evidencia GDPR).
- **change-email** (2 pasos):
  1. `change-email`: valida que `new_email` este libre; si el user tiene
     password la valida (argon2); genera un magic-link kind=`email-change`
     (token opaco, hash SHA-256 en `auth_magic_links`, `new_email` en
     `metadata`); publica el email de confirmacion (kind
     `email-change-verify`) al email NUEVO; devuelve `200 {request_id,
     expires_in: 900}`.
  2. `confirm-email-change` (PUBLICO, token-based): consume el magic-link
     (single-use, vigente), valida que el nuevo email siga libre, UPDATE
     `auth_users.email`, notifica al email VIEJO (kind `email-changed`),
     audita `profile.change-email.confirmed`.
- **delete-account** (GDPR): sentinel exacto `DELETE-MY-ACCOUNT`. UPDATE
  `deleted_at` + anonimiza `email = deleted-<id>@invalid.local` + DELETE
  explicitos en credentials/mfa/recovery/webauthn/email_codes/magic_links
  + borra las sesiones + blacklistea sus families en DDB. **Guard AC-29**:
  si el email del user esta en la whitelist `admin-emails`, devuelve
  `409 CANNOT_DELETE_ADMIN_ACCOUNT` (el ultimo admin no se borra a si
  mismo; primero hay que sacar su email del SSM).

> **Soft-delete = UPDATE, no DELETE de la fila**. Las FK ON DELETE CASCADE
> reaccionan a DELETE, no a UPDATE, y los modelos auth NO declaran
> `relationship()`. Por eso `soft_delete_user` borra cada tabla hija con
> `delete(Model).where(Model.user_id == X)` explicito. El re-uso del email
> tras soft-delete lo habilita el partial unique index
> `ux_auth_users_email_active` (WHERE deleted_at IS NULL).

## Status

- **get**: `{status, mfa_configured, mfa_methods, webauthn_count,
  recovery_codes_remaining, failed_attempts, locked_until}`. El
  `count_active_mfa` es transversal (mfa_methods + webauthn).
- **list-sessions**: lee `auth_user_sessions`, ordena por last_active_at
  DESC, marca `current: true` la sesion cuyo `family_id` coincide con el
  del access JWT en curso. Ver [08-sessions](08-sessions.md).
- **revoke-session**: borra una sesion (dual filter por user_id) +
  blacklistea su family. NO permite revocar la sesion actual
  (`400 CANNOT_REVOKE_CURRENT_SESSION` -> usar `auth.session.logout`).

## require_active_user del Lambda `users` (≠ auth)

El `require_active_user` de `users` (en `core/services/jwt_service.py`)
distingue, a diferencia del de `auth` (que devuelve 401 para todo no-ACTIVE):

- header ausente / JWT invalido o revocado / user inexistente o
  soft-deleted -> **401**.
- user `disabled` -> **403 `ACCOUNT_DISABLED`** (JWT valido, cuenta
  bloqueada — AC-16).
- user `locked` -> **403 `ACCOUNT_LOCKED`**.

`authenticate(authorization)` devuelve `(user, claims)` para que
`status.*` lea `claims.family_id` (la sesion en curso).

## Rate-limit

Per-IP (el `endpoint` es la dimension; ej. `/users#profile.update`).
`turnstile_validated=False` SIEMPRE (endpoints JWT-authed sin Turnstile;
pasar True auto-blacklistearia a un user que haga 3+ requests/60s).

## Infra

manifest `services/users/manifest.yaml`: `POST /users`, snap_start,
memory 384, queues `auth-email` (producer), tables `rate-limit-rules`,
`rate-limit-buckets`, `jwt-blacklist`, secrets `neon-url`, `jwt-secret`,
`admin-emails`, `ses-from-address`. `sends-email: false` (publica a SQS).

[↑ README](README.md)
