# Plan 03: Auth users management — Lambda `users` con profile / status / admin

> **Orden en la serie auth**: este es el **3 de 3** planes secuenciales.
>
> ```text
> 01 — auth-infra-basics       (DEPENDENCIA: shared.auth + schema + lambda auth basico)
> 02 — auth-mfa                (DEPENDENCIA: MFA / WebAuthn agregados al lambda auth)
> 03 — auth-users-management   <-- ESTE PLAN (lambda `users` separado)
> ```
>
> **Dependencia dura**: requiere planes 01 + 02 mergeados a `dev`
> (idealmente `main`). Este plan agrega el segundo Lambda solicitado
> originalmente por el usuario, `users`, separando la gestion del
> identity (CRUD del perfil + status + admin) del ciclo de autenticacion
> (`auth`).

## Que entrega este plan

- **Schema Neon (migration 00000004)**: agrega columnas a `auth_users`
  (display_name, locale, timezone, marketing_consent, deleted_at) y
  3 tablas nuevas:
  - `auth_user_sessions`: tracking de sesiones activas por user
    (refresh_token family_id + device info + last_active_at). Permite
    listar y cerrar sesiones individuales.
  - `auth_user_admin_actions`: audit de acciones administrativas
    sobre users (disable, force_logout, delete, restore).
  - `auth_user_consent_log`: log de cambios de marketing_consent +
    privacy_policy_version para GDPR.
- **Shared subpackage `shared.auth` (extension menor)**: agrega
  `is_admin(user)` helper basado en role o lista whitelist en SSM.
- **Lambda `users` (NUEVO)**: HTTP `POST /users`. 3 operations:
  - `profile.*`: get, update (display_name, locale, timezone,
    marketing_consent), change-email (con re-verificacion),
    delete-account (soft delete).
  - `status.*`: get (devuelve el self status), list-sessions,
    revoke-session (logout de un device).
  - `admin.*`: scope solo para Pablo (whitelist por email):
    list-users (paginado), get-user, disable-user, enable-user,
    force-logout, delete-user (hard delete con cascada audit),
    list-admin-actions.
- **Integracion con `auth`**: el Lambda `auth` queda intocable. Las
  acciones admin (`disable-user`) actualizan `auth_users.status =
  disabled` -> el siguiente login de ese user devuelve `401
  ACCOUNT_DISABLED` (logica que ya esta en `auth.login.start` desde
  plan 01).
- **Rate-limit**: reglas nuevas para `users#*` (mas relajadas que auth
  porque requieren access JWT).
- **Audit**: todas las operations admin escriben a
  `auth_user_admin_actions` ademas del `auth_audit_log` general.

## Que NO entrega este plan

- Frontend Astro (signup / signin / dashboard / settings) -> plan
  futuro.
- Email worker plantillas para "tu cuenta fue deshabilitada", "cambio
  de email confirmado" -> agregar al `auth_email_worker` en este plan
  (incremental al worker, no es Lambda nuevo).
- Bulk operations admin (importar lista de users, exportar CSV) ->
  fuera de scope.
- 2FA-enforce-per-organization features (no aplica al portfolio).

## Cuando leer

| Tema | Archivo |
|------|---------|
| Problema, solucion, AC numerados | [01-contexto-y-decision.md](01-contexto-y-decision.md) |
| Schema Neon: columnas nuevas en `auth_users` + 3 tablas nuevas | [02-schema-neon-users.md](02-schema-neon-users.md) |
| Shared / Admin whitelist | [03-shared-and-admin.md](03-shared-and-admin.md) |
| Infraestructura: SSM admin-emails + email-worker plantillas | [04-infraestructura.md](04-infraestructura.md) |
| Arquitectura del Lambda `users`: operations profile/status/admin | [05-lambda-users-arquitectura.md](05-lambda-users-arquitectura.md) |
| Testing (unit + integration + admin authz) | [06-testing.md](06-testing.md) |
| Archivos afectados con verificacion por archivo | [07-archivos-afectados.md](07-archivos-afectados.md) |
| Descomposicion en tareas atomicas | [08-descomposicion-paralelizacion.md](08-descomposicion-paralelizacion.md) |
| Commits incrementales | [09-commits.md](09-commits.md) |
| Paralelizacion con git worktrees | [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) |
| Verificacion E2E iterativa | [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Estado por fase

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Planes 01 + 02 mergeados a `dev` (prerequisito) | pending |
| 1 | Plan escrito + claude docs | pending |
| 2 | Schema Neon (migration 00000004 con columnas nuevas + 3 tablas) | pending |
| 3 | `shared.auth` extension `is_admin` + `require_admin` helper | pending |
| 4 | SSM `/portfolio/${stage}/admin-emails` (lista de emails admin) | pending |
| 5 | `auth_email_worker` extension: 3 plantillas nuevas | pending |
| 6 | Lambda `users` scaffold (manifest + AppConfig + handler + EventModel) | pending |
| 7 | Operation `profile` (get/update/change-email/delete-account) | pending |
| 8 | Operation `status` (get/list-sessions/revoke-session) | pending |
| 9 | Operation `admin` (list-users, get-user, disable, enable, force-logout, delete, list-actions) | pending |
| 10 | Rate-limit rules + integracion + tests integration | pending |
| 11 | Verificacion E2E + actualizacion ER + limpieza spec | pending |

## Decisiones no-reabribles

1. **Lambda separada `users`**: el split solicitado en el dialogo
   original. Mismo API Gateway que `auth` (path `/users`). Mismo
   patron `operation + action` + http_handler.
2. **Admin authz por email whitelist en SSM**: `/portfolio/${stage}/admin-emails`
   (SecureString, lista coma-separada). El handler `require_admin` lee
   el SSM y compara contra `user.email` del JWT. Alternativa
   considerada (role enum en `auth_users.role`) rechazada por
   simplicidad: solo Pablo es admin y queremos rotacion sin tocar DB.
3. **Soft-delete del user**: `auth_users.deleted_at` timestamp. Login
   con email de un user soft-deleted devuelve `404 EMAIL_NOT_FOUND`
   (se comporta como inexistente). El email queda libre para
   re-registro (con CITEXT unique + WHERE `deleted_at IS NULL`). Hard
   delete es admin-only.
4. **Sesiones activas por refresh_token family_id**: cuando el lambda
   `auth` emite un refresh_token con `family_id=<X>`, INSERT en
   `auth_user_sessions(user_id, family_id, device_info, ip,
   last_active_at)`. Cada refresh actualiza `last_active_at`. Logout
   borra el row (cascade del blacklist family).
5. **change-email flujo en dos pasos**: el user pide cambio, recibe
   magic-link al email NUEVO, al confirmar actualiza `auth_users.email`.
   Nuevo email tabla efimera `auth_user_email_change_requests` (no,
   simpler: reusar `auth_magic_links` con `kind='email-change'` agregado
   al enum existente — preferencia).
6. **Status del user devuelto al frontend**: enum:
   - `pending`: registro iniciado, email no verificado.
   - `active`: operativo.
   - `disabled`: deshabilitado por admin.
   - `locked`: bloqueo automatico (10 fallos consecutivos / hora).
   - `deleted`: soft-deleted.
   El frontend usa esto para decidir que mostrar (mensaje al user).
7. **Admin actions audit obligatorio**: cada admin operation
   (`admin.disable-user`, etc.) inserta row en
   `auth_user_admin_actions(admin_user_id, target_user_id, action,
   metadata, ip, created_at)`. Inmutable.
8. **GDPR delete-account**: el `profile.delete-account` (self-service)
   marca `deleted_at`, anonimiza `email` a `deleted-<id>@invalid.local`
   y borra `auth_credentials`, `auth_mfa_methods`, etc. en cascade.
   Conserva `auth_audit_log` y `auth_user_admin_actions` para
   compliance (sin PII personal). En 30 dias, hard-delete
   programatico via cron Lambda (NO en scope de este plan, planificado).
9. **list-users paginado**: cursor-based con `last_id` (uuidv7
   ordenable). page_size default 50, max 200.

## Reglas criticas (siempre activas)

- **SIEMPRE** `require_admin` valida via SSM admin-emails (no
  hardcodear el email de Pablo en el codigo).
- **SIEMPRE** `admin.*` operations escriben a `auth_user_admin_actions`
  ANTES de la accion destructiva (audit pre-hoc).
- **SIEMPRE** un user NO admin que intente `admin.*` recibe `404
  NOT_FOUND` (no `403 FORBIDDEN`) — defensa contra enumeration.
- **SIEMPRE** `profile.update` solo modifica campos del propio user
  (validado por `user.id == claims.sub`).
- **SIEMPRE** `disable-user` no afecta el JWT vivo del target — el
  proximo `session.refresh` o cualquier operacion verifica
  `auth_users.status` y deniega. Para invalidacion inmediata, llamar
  tambien `admin.force-logout`.
- **NUNCA** un admin puede ver el password_hash, TOTP secret o
  recovery codes hash de otro user (solo metadata).
- **NUNCA** un user puede `delete-account` si tiene roles administrativos
  asignados (no aplica hoy: si Pablo intenta, hay que asignar admin a
  otro email primero — guard).
- **NUNCA** retornar `email` de otro user en respuestas no-admin.

## Matriz de verificacion (rapida)

| Capa | Comando |
|------|---------|
| Sintaxis | `python -m compileall -q serverless/lambda/services/users` |
| Imports shared-only | `serverless lint-deps --lambda=users` |
| Tests unit | `serverless tests --type=unit --lambda=users` |
| Tests integration | `serverless tests --type=integration --lambda=users` |
| Migration up dev | `serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev` |
| Run local | `serverless run --stage=local --lambda=users --event=events/profile-get.json` |
| Deploy dev | `serverless deploy --lambda=users --stage=dev --aws-profile=tfs-dev` |
| Smoke E2E | ver [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Bibliografia interna

- Planes 01 + 02 (precursores). Al cierre del plan 03, sus carpetas
  ya estan eliminadas del repo; referencia via `git log`.
- `.claude/docs/auth-system/` — documentacion permanente; este plan
  agrega capitulos sobre users y admin.
- `.claude/rules/lambda-controller.md`, `lambda-shared-imports.md`,
  `neon-management.md`, `serverless-secrets.md`,
  `ci-cd-pipeline.md`.
