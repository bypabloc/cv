# 06. Estrategia de testing — plan 03

> Hereda el patron de los planes 01 y 02. Tests nuevos enfocados en
> profile / status / admin authz.

## Tests unit `shared.auth.admin` (en shared/tests/)

Listados en [03-shared-and-admin.md](03-shared-and-admin.md): 11
archivos.

## Tests unit `shared/db/repositories/auth_users.py`

| Archivo | Escenario |
|---------|-----------|
| `test_update_profile_partial.py` | UPDATE solo campos presentes |
| `test_soft_delete_anonymizes_email.py` | email -> deleted-<id>@invalid.local |
| `test_partial_unique_email_allows_reuse.py` | tras soft-delete, INSERT con mismo email OK |
| `test_hard_delete_cascades.py` | DELETE auth_users -> cascada en credenciales/mfa/etc. |
| `test_list_users_paginated_by_cursor.py` | cursor=last_id retorna siguientes 50 |
| `test_list_users_status_filter.py` | filtro disabled retorna solo esos |
| `test_insert_user_session.py` | INSERT con family_id UK |
| `test_update_session_activity.py` | UPDATE last_active_at |
| `test_rotate_session_family_id.py` | UPDATE family_id viejo -> nuevo |
| `test_revoke_all_user_sessions_returns_families.py` | DELETE + retorna list[family_id] |
| `test_insert_admin_action.py` | INSERT row con metadata jsonb |
| `test_list_admin_actions_paginated.py` | range from/to + ordering |
| `test_insert_consent_log.py` | INSERT con old/new value |

## Tests unit del Lambda `users`

### `services/` (~30 archivos)

| Archivo | Escenario |
|---------|-----------|
| `test_profile_service_get_by_id.py` | retorna user con relations |
| `test_profile_service_update_partial.py` | parcial OK |
| `test_profile_service_change_email_new_email_available.py` | INSERT magic_link |
| `test_profile_service_change_email_taken.py` | levanta EmailAlreadyInUseError |
| `test_profile_service_soft_delete_anonymizes.py` | email anonimo + cascade |
| `test_profile_service_disable_active.py` | UPDATE status=disabled |
| `test_profile_service_enable_disabled.py` | UPDATE status=active |
| `test_profile_service_enable_active_no_op.py` | no cambia si ya active |
| `test_session_service_list_with_current_flag.py` | marca current=true para el access JWT |
| `test_session_service_revoke_blacklists_family.py` | DELETE + DDB PutItem family blacklist |
| `test_admin_service_require_admin_ok.py` | admin email pasa |
| `test_admin_service_require_admin_not_admin_raises_404.py` | NOT_FOUND code=4040 |
| `test_audit_admin_service_log.py` | INSERT row con metadata correcto |
| `test_consent_service_log.py` | INSERT row |
| `test_blacklist_service_blacklist_family.py` | Query GSI by_family_id + PutItem en cada jti |
| `test_jwt_service_require_active_user_ok.py` | access JWT valido + user active -> retorna user |
| `test_jwt_service_require_active_user_disabled.py` | user disabled -> ApplicationError |
| `test_jwt_service_require_active_user_deleted.py` | user deleted -> ApplicationError |
| `test_email_dispatch_service_publish_email_changed.py` | SQS SendMessage con kind=email-changed |
| `test_email_dispatch_service_publish_account_disabled.py` | idem |

### `controllers/` (~25 archivos)

| Archivo | AC | Escenario |
|---------|-----|-----------|
| `test_profile_get_ok.py` | AC-1 | retorna profile completo |
| `test_profile_get_no_auth.py` | — | 401 sin Authorization |
| `test_profile_update_partial_ok.py` | AC-2 | UPDATE solo display_name |
| `test_profile_update_full_ok.py` | AC-2 | UPDATE todos los campos |
| `test_profile_update_invalid_locale.py` | — | 400 ValidationError |
| `test_profile_update_marketing_consent_logs.py` | AC-3 | INSERT consent_log |
| `test_profile_update_marketing_consent_same_no_log.py` | — | sin INSERT (no cambio) |
| `test_profile_change_email_ok.py` | AC-4 | magic_link + SQS |
| `test_profile_change_email_already_in_use.py` | — | 409 |
| `test_profile_change_email_wrong_password.py` | — | 401 INVALID_PASSWORD |
| `test_profile_delete_account_ok.py` | AC-6 | soft-delete + cascade + blacklist |
| `test_profile_delete_account_wrong_confirm.py` | — | 400 INVALID_CONFIRM_SENTINEL |
| `test_status_get_ok.py` | AC-7 | retorna info correcta |
| `test_status_list_sessions_ok.py` | AC-8 | ordenado last_active_at DESC, current marcado |
| `test_status_revoke_session_ok.py` | AC-9 | DELETE + blacklist |
| `test_status_revoke_session_current_fails.py` | AC-10 | CANNOT_REVOKE_CURRENT_SESSION |
| `test_admin_list_users_not_admin_404.py` | AC-11 | NOT_FOUND |
| `test_admin_list_users_admin_ok.py` | AC-12 | 50 users + cursor |
| `test_admin_list_users_paginated.py` | AC-13 | cursor + page_size respetados |
| `test_admin_get_user_ok.py` | AC-14 | detalle con relations |
| `test_admin_disable_user_ok.py` | AC-15 | UPDATE + admin_action row |
| `test_admin_disable_self_fails.py` | — | CANNOT_DISABLE_SELF |
| `test_admin_enable_user_ok.py` | AC-17 | UPDATE + audit |
| `test_admin_force_logout_ok.py` | AC-18 | DELETE all sessions + blacklist families |
| `test_admin_delete_user_ok.py` | AC-19 | cascade + audit |
| `test_admin_delete_user_wrong_sentinel.py` | — | INVALID_CONFIRM_SENTINEL |
| `test_admin_delete_self_fails.py` | — | CANNOT_DELETE_SELF |
| `test_admin_list_admin_actions_ok.py` | AC-20 | range + pagination |
| `test_admin_empty_whitelist_returns_404.py` | AC-21 | si admin-emails='' SSM, 404 |

### `models/` (~10 archivos)

| Archivo | Escenario |
|---------|-----------|
| `test_profile_update_in_locale_enum.py` | locale no en {es,en} -> ValidationError |
| `test_profile_update_in_display_name_max_64.py` | > 64 chars -> ValidationError |
| `test_profile_change_email_in_email_format.py` | not email -> ValidationError |
| `test_profile_delete_account_in_sentinel_exact.py` | confirm != exact -> ValidationError |
| `test_admin_disable_user_in_uuid.py` | user_id no UUID -> ValidationError |
| `test_admin_delete_user_in_sentinel_matches_user_id.py` | confirm no matchea -> ValidationError |
| `test_admin_list_users_in_page_size_max.py` | > 200 -> ValidationError |

## Tests integration

| Archivo | Escenario |
|---------|-----------|
| `test_profile_update_full_flow_e2e.py` | register + update + verify update reflected |
| `test_profile_change_email_full_flow_e2e.py` | inicia + click magic-link + login con nuevo email OK |
| `test_profile_delete_account_full_flow_e2e.py` | delete + verify login imposible |
| `test_status_list_sessions_multi_device_e2e.py` | login desde 2 "dispositivos" (2 calls a auth) + status.list muestra 2 |
| `test_admin_disable_then_login_e2e.py` | admin disables + target intenta login -> 403 (AC-16) |
| `test_admin_force_logout_e2e.py` | admin force_logout + target con access JWT viejo -> 401 |
| `test_admin_delete_user_cascade_e2e.py` | admin delete + verify cascada en credenciales/mfa |
| `test_email_reuse_after_soft_delete_e2e.py` | AC-27: soft-delete + re-register con mismo email |
| `test_migration_00000004_up_down_e2e.py` | AC-25 |

## Tests integration tambien al lambda `auth` (sessions tracking)

| Archivo (en `services/auth/tests/integration/`) | Escenario |
|---------|-----------|
| `test_session_tracking_create_on_login_e2e.py` | tras login.verify-code -> auth_user_sessions row creado |
| `test_session_tracking_rotates_on_refresh_e2e.py` | session.refresh -> family_id rota en row |
| `test_session_tracking_deletes_on_logout_e2e.py` | session.logout -> row deleted |
| `test_session_tracking_persists_across_refresh_e2e.py` | 5 refresh -> 1 solo row (same family) |

## Cobertura objetivo

- Lambda `users`: >= 85% per-file en `core/{services,controllers,models}/`.
- shared.auth.admin: 100% (modulo chico).
- shared/db/repositories/auth_users.py: 90%+.

## Comandos

```bash
# unit
python devtools/run.py serverless tests --type=unit --lambda=users
python devtools/run.py serverless tests --type=unit --shared

# coverage
python devtools/run.py serverless tests --type=coverage --lambda=users

# integration (con AWS dev + Neon dev)
python devtools/run.py serverless tests --type=integration --lambda=users
python devtools/run.py serverless tests --type=integration --lambda=auth
```

## Reglas duras

- **SIEMPRE** test admin authz incluye un caso "no admin" -> 404
  (no 403).
- **SIEMPRE** test de `delete-account` verifica:
  (a) email anonimizado,
  (b) credentials/mfa borrados,
  (c) JWT blacklisted en DDB,
  (d) auth_audit_log preservado.
- **SIEMPRE** mock SSM `admin-emails` con admin email del test fixture.
- **SIEMPRE** los tests que toquen `shared.auth.admin.is_admin` /
  `load_admin_emails` (directa o transitivamente) deben **resetear
  el cache module-level** antes y despues. Patron recomendado:
  fixture `autouse=True` en `shared/tests/unit/shared/auth/conftest.py`
  que llame a `shared.auth.admin._CACHE.update({'emails':
  frozenset(), 'expires_at': 0.0})`. Sin esto, el orden de tests
  cambia el resultado (cache hit de un test anterior con emails
  mockeados distintos).
- **SIEMPRE** test de `delete-account` con AC-29 verifica: si el
  user esta en `admin-emails`, recibe `409 CANNOT_DELETE_ADMIN_ACCOUNT`
  y NO se borra nada.
- **NUNCA** test de admin contra un user real del repo (usar fixtures
  con uuidv7 nuevos).
