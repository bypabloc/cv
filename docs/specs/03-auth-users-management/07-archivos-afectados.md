# 07. Archivos Afectados — plan 03

## Crear

### Migration + modelos

- `serverless/lambda/shared/db/alembic/versions/00000004_auth_users_extension.py`
- `serverless/lambda/shared/db/models/auth/user_session.py`
- `serverless/lambda/shared/db/models/auth/admin_action.py`
- `serverless/lambda/shared/db/models/auth/consent_log.py`
- `serverless/lambda/shared/db/repositories/auth_users.py` — separa
  helpers del plan 01 + agrega 15+ nuevos.
- tests `shared/tests/unit/shared/db/repositories/test_auth_users_*.py` (~13).
  - Verificar: `serverless tests --type=unit --shared`, branch Neon
    de prueba para AC-25.

### shared.auth.admin

- `serverless/lambda/shared/auth/admin.py`
- `serverless/lambda/shared/auth/__init__.py` (modificar — agregar
  exports).
- tests `shared/tests/unit/shared/auth/test_admin_*.py` (11).

### Infra

- `serverless/lambda/resources/secrets/admin-emails.yaml`.

### auth_email_worker — extension

- `services/auth_email_worker/core/controllers/email/email_changed.py`
- `services/auth_email_worker/core/controllers/email/account_disabled.py`
- `services/auth_email_worker/core/controllers/email/account_deleted.py`
- `services/auth_email_worker/core/templates/{es,en}/email-changed.{txt,html}` (4 archivos)
- `services/auth_email_worker/core/templates/{es,en}/account-disabled.{txt,html}` (4)
- `services/auth_email_worker/core/templates/{es,en}/account-deleted.{txt,html}` (4)
- `services/auth_email_worker/core/settings/operations.py` — MODIFICAR
  agregando los 3 nuevos kinds.
- `services/auth_email_worker/core/models/email.py` — MODIFICAR
  agregando schemas Pydantic para los 3 nuevos kinds.
- tests `services/auth_email_worker/tests/unit/test_worker_handles_email_changed.py` y los otros 2 (3 archivos).
  - Verificar: `serverless tests --type=unit --lambda=auth_email_worker`.

### Lambda `users` (NUEVO)

- `services/users/manifest.yaml`
- `services/users/pyproject.toml`
- `services/users/uv.lock`
- `services/users/.gitignore`
- `services/users/core/handler.py`
- `services/users/core/settings/{config,operations}.py`
- `services/users/core/models/{event,profile,status,admin}.py`
- `services/users/core/controllers/profile/{get,update,change_email,delete_account}.py`
- `services/users/core/controllers/status/{get,list_sessions,revoke_session}.py`
- `services/users/core/controllers/admin/{list_users,get_user,disable_user,enable_user,force_logout,delete_user,list_admin_actions}.py`
- `services/users/core/services/{profile,session,admin,audit_admin,consent,blacklist,jwt,email_dispatch,audit,rate_limit}_service.py`
- `services/users/events/*.json` (14 archivos, uno por action).
- `services/users/tests/unit/...` (~75 archivos).
- `services/users/tests/integration/...` (~9 archivos).
  - Verificar:
    `serverless lint-deps --lambda=users`
    `serverless tests --type=unit --lambda=users`
    `serverless tests --type=coverage --lambda=users` (>= 85%)

### Documentacion permanente

- `.claude/docs/auth-system/06-users.md` (profile, status).
- `.claude/docs/auth-system/07-admin.md` (whitelist, admin actions,
  audit).
- `.claude/docs/auth-system/08-sessions.md` (tracking via
  auth_user_sessions, multi-device).
- `.claude/rules/auth-system.md` — MODIFICAR agregando secciones
  users + admin.
- `.claude/skills/auth-system/SKILL.md` — MODIFICAR keywords para
  incluir `profile`, `status`, `admin`, `perfil`, `gestion de usuarios`,
  `sesiones activas`, `panel admin`.

## Modificar

- `docs/diagrams/db-er.mmd` — agregar columnas nuevas en `auth_users`
  + 3 tablas nuevas + relaciones.
- `docs/specs/03-auth-users-management/` — esta carpeta (efimera, se
  elimina al cerrar).

### En el Lambda `auth` (sessions tracking)

- `services/auth/core/services/session_tracking_service.py` — NUEVO
  helper.
- 10 controllers modificados con inyeccion minima del helper
  (2-3 lineas en `execute()`):
  - `controllers/register/verify_magic_link.py` (on_session_created)
  - `controllers/register/verify_code.py` (on_session_created)
  - `controllers/login/verify_magic_link.py` (on_session_created)
  - `controllers/login/verify_code.py` (on_session_created)
  - `controllers/login/verify_password.py` (on_session_created)
  - `controllers/login/verify_totp.py` (on_session_created)
  - `controllers/webauthn/login_verify.py` (on_session_created)
  - `controllers/mfa/recovery_codes_consume.py` (on_session_created)
  - `controllers/session/refresh.py` (on_session_rotated, rotation)
  - `controllers/session/logout.py` (on_session_revoked, DELETE)
- tests adicionales `services/auth/tests/integration/test_session_tracking_*.py` (4).

### En el shared.db

- `shared/db/models/auth/user.py` — MODIFICAR agregando columnas
  nuevas + indices.
- `shared/db/models/auth/enums.py` — MODIFICAR agregando
  `email-change` a `AuthLinkKind`.
- `shared/db/models/auth/__init__.py` — MODIFICAR re-exports.
- `shared/db/repositories/auth.py` (existente) — sin cambios; los
  nuevos helpers viven en `auth_users.py`.

## Eliminar

- `docs/specs/03-auth-users-management/` — al cerrar (ultimo commit).

## NO se toca

- Frontend Astro.
- Lambdas `cv`, `contact_form`, `contact_worker`, `tracking_pixel`,
  `tracking_worker`, `stream_processor`, `db`.
- Shared subpackages `core`, `aws`, `http`, `observability`,
  `rate_limit`, `cache`, `dynamodb`, `lambda_kit` (sin cambios en este
  plan).
- `.github/workflows/*.yml`.

## Resumen contable

Recuento item-por-item (todos los archivos del plan, separando
`Crear` / `Modificar` / `Eliminar` por subcategoria):

| Categoria | Crear | Modificar | Eliminar | Total |
|-----------|-------|-----------|----------|-------|
| Migration alembic + 3 modelos nuevos + 1 repo + 13 tests repos | 18 | 3 (user.py + enums.py + auth/__init__.py) | 0 | 21 |
| `shared.auth.admin` (admin.py + 11 tests) | 12 | 1 (`shared/auth/__init__.py`) | 0 | 13 |
| Infra resources (admin-emails.yaml) | 1 | 0 | 0 | 1 |
| auth_email_worker extension (3 controllers + 12 templates + 3 tests) | 18 | 2 (operations.py + email.py) | 0 | 20 |
| Lambda `users` scaffold (manifest+pyproject+uv.lock+.gitignore) | 4 | 0 | 0 | 4 |
| Lambda `users` core (handler + 2 settings + 4 models + 14 controllers + 10 services) | 31 | 0 | 0 | 31 |
| Lambda `users` events JSON (1 por action) | 14 | 0 | 0 | 14 |
| Lambda `users` tests unit (services ~30 + controllers ~25 + models ~10 + helpers) | ~70 | 0 | 0 | ~70 |
| Lambda `users` tests integration | 9 | 0 | 0 | 9 |
| Lambda `auth` sessions tracking (1 helper + tests integration) | 5 (1 service + 4 tests) | 8 (4 verify-* + refresh + logout + webauthn.login_verify + mfa.recovery_codes_consume) | 0 | 13 |
| Documentacion permanente (.claude/) (3 docs nuevos + rule + skill) | 3 | 2 | 0 | 5 |
| Plan efimero (`docs/specs/03-...`) | 12 | 0 | -12 | 0 |
| Diagrama ER | 0 | 1 | 0 | 1 |
| __Total neto__ | __~197__ | __~17__ | __-12__ | __~202 archivos tocados__ |

> __Nota__: las cifras de tests unit (`~70` para users, `13` para
> repos shared, `11` para admin) son aproximadas — la enumeracion
> exacta vive en [06-testing.md](06-testing.md). El total real puede
> variar +/- 5% segun se desagreguen casos parametrizados o se
> consoliden helpers compartidos en `tests/unit/_helpers.py`.
>
> __Conteo viejo__ decia "~158 archivos nuevos" — subestimaba el
> Lambda `users` (85 vs ~128 reales) y omitia desagregar
> modelos/repos. El numero correcto es __~202__.
