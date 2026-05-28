# 08. Descomposicion para Paralelizacion — plan 03

> Plan **Large** (~158 archivos). 12 tareas atomicas.

## Grafo de dependencias

```text
T1 plan + claude docs                          (raiz)
  |
  +--> T2 shared.auth.admin                    (raiz tras T1)
  |
  +--> T3 schema Neon (migration + modelos + repos)   (raiz tras T1)
  |
  +--> T4 infra (SSM admin-emails + sync)       (raiz tras T1)
  |
  +--> T5 auth_email_worker extension          (raiz tras T1; indep)
  |     (3 controllers + 12 plantillas)
  |
  +--> T6 lambda users scaffold + services      (depende T2 + T3 + T4)
  |     (manifest + AppConfig + handler + EventModel + services internos)
  |
  +--> T7 controllers profile/                 (depende T6)
  |     (paralelo con T8, T9)
  |
  +--> T8 controllers status/                  (depende T6)
  |     (paralelo con T7, T9)
  |
  +--> T9 controllers admin/                   (depende T6 + T2)
  |     (paralelo con T7, T8)
  |
  +--> T10 sessions tracking en lambda auth     (depende T3; modifica auth)
  |     (paralelo con T7-T9 si el merge se ordena bien)
  |
  +--> T11 rate-limit seed + deploys           (depende T7..T10)
  |
  +--> T12 verificacion E2E + ER + cleanup     (seccion 11; final)
```

## Tareas

### T1: Plan + claude docs

- **Archivos**:
  - `docs/specs/03-auth-users-management/*.md` (12).
  - `.claude/docs/auth-system/{06-users,07-admin,08-sessions}.md`
  - `.claude/rules/auth-system.md` (modificar).
  - `.claude/skills/auth-system/SKILL.md` (modificar keywords).
- **AC**: ninguna.
- **Depende de**: ninguna.
- **Paralelizable con**: ninguna.
- **Verify**: markdownlint + skill validation (`claude -p`).
- **Done**: spec + docs/claude commiteados.

### T2: shared.auth.admin

- **Archivos**:
  - `shared/auth/admin.py`
  - `shared/auth/__init__.py` (modificar)
  - `shared/tests/unit/shared/auth/test_admin_*.py` (11)
- **AC**: soporta AC-11, AC-12, AC-21.
- **Depende de**: T1.
- **Paralelizable con**: T3, T4, T5.
- **Verify**:
  `serverless lint-deps --shared`
  `serverless tests --type=unit --shared`
- **Done**: 11 tests verdes, coverage 100% en `admin.py`.

### T3: Schema Neon + modelos + repositories

- **Archivos**:
  - `shared/db/alembic/versions/00000004_auth_users_extension.py`
  - `shared/db/models/auth/{user_session,admin_action,consent_log}.py`
  - `shared/db/models/auth/user.py` (modificar)
  - `shared/db/models/auth/enums.py` (modificar — agregar `email-change`)
  - `shared/db/models/auth/__init__.py` (modificar)
  - `shared/db/repositories/auth_users.py` (NUEVO, 15+ helpers)
  - tests (~13)
- **AC**: AC-22..AC-25.
- **Depende de**: T1.
- **Paralelizable con**: T2, T4, T5.
- **Verify**:
  - Branch Neon de prueba: up -> down -> up idempotente.
  - `serverless tests --type=unit --shared`
- **Done**: migration aplica + reverte, 13 tests verdes.

### T4: Infra (SSM admin-emails)

- **Archivos**:
  - `resources/secrets/admin-emails.yaml`
- **AC**: soporta AC-11, AC-21.
- **Depende de**: T1.
- **Paralelizable con**: T2, T3, T5.
- **Verify**:
  `serverless validate-catalog --stage=dev`
  `serverless provision-infra --stage=dev --aws-profile=tfs-dev` (crea
    el SSM)
  `serverless sync-secrets --stage=dev --aws-profile=tfs-dev` (publica
    `ADMIN_EMAILS=pacg1991@gmail.com`)
- **Done**: SSM existe + valor sincronizado.

### T5: auth_email_worker extension

- **Archivos**:
  - `services/auth_email_worker/core/controllers/email/{email_changed,account_disabled,account_deleted}.py`
  - 12 templates en es/ y en/
  - `core/settings/operations.py` (modificar)
  - `core/models/email.py` (modificar)
  - 3 tests
- **AC**: ninguna directa (soporta plan funcional).
- **Depende de**: T1.
- **Paralelizable con**: T2, T3, T4.
- **Verify**:
  `serverless tests --type=unit --lambda=auth_email_worker`
  `serverless run --stage=local --lambda=auth_email_worker --event=events/email-changed.json`
- **Done**: 3 controllers + 12 templates + 3 tests verdes.

### T6: Lambda `users` scaffold + services

- **Archivos**:
  - `services/users/{manifest.yaml, pyproject.toml, uv.lock, .gitignore}`
  - `core/handler.py`
  - `core/settings/{config,operations}.py`
  - `core/models/event.py`
  - `core/services/{profile,session,admin,audit_admin,consent,blacklist,jwt,email_dispatch,audit,rate_limit}_service.py`
  - `core/models/{profile,status,admin}.py`
  - tests services (~25)
  - tests models (~10)
- **AC**: transversal.
- **Depende de**: T2, T3, T4.
- **Paralelizable con**: T5.
- **Verify**:
  `serverless lint-deps --lambda=users`
  `serverless tests --type=unit --lambda=users` (35 tests verdes)
- **Done**: scaffold + services + models verdes.

### T7: Controllers profile/ (paralelo con T8, T9)

- **Archivos**:
  - `core/controllers/profile/{get,update,change_email,delete_account}.py`
  - 4 events JSON
  - ~10 tests controllers
- **AC**: AC-1..AC-6, AC-26.
- **Depende de**: T6.
- **Paralelizable con**: T8, T9.
- **Verify**: `serverless tests --type=unit --lambda=users`.
- **Done**: 4 controllers + 10 tests verdes.

### T8: Controllers status/ (paralelo con T7, T9)

- **Archivos**:
  - `core/controllers/status/{get,list_sessions,revoke_session}.py`
  - 3 events JSON
  - ~4 tests
- **AC**: AC-7..AC-10.
- **Depende de**: T6.
- **Paralelizable con**: T7, T9.
- **Verify**: idem.
- **Done**: 3 controllers + 4 tests.

### T9: Controllers admin/ (paralelo con T7, T8)

- **Archivos**:
  - `core/controllers/admin/{list_users,get_user,disable_user,enable_user,force_logout,delete_user,list_admin_actions}.py`
  - 7 events JSON
  - ~13 tests
- **AC**: AC-11..AC-21, AC-28.
- **Depende de**: T2 (require_admin), T6.
- **Paralelizable con**: T7, T8.
- **Verify**: idem.
- **Done**: 7 controllers + 13 tests verdes.

### T10: Sessions tracking en lambda auth

- **Archivos**:
  - `services/auth/core/services/session_tracking_service.py` (NUEVO)
  - 8 modificaciones (4 verify-* + refresh + logout + 2 mas)
  - 4 tests integration nuevos en `services/auth/tests/integration/`
- **AC**: AC-22..AC-24.
- **Depende de**: T3 (auth_user_sessions table).
- **Paralelizable con**: T7, T8, T9 (toca lambda DISTINTO — auth, no
  users).
- **Verify**:
  `serverless tests --type=unit --lambda=auth` (los unit tests del
  auth no deben regresionar)
  `serverless tests --type=integration --lambda=auth` (con AWS dev).
- **Done**: 4 integration tests verdes + 8 archivos integran helper
  sin romper tests del plan 01/02.

### T11: Rate-limit seed + deploys

- **Archivos**: ninguno (operativo) o pequenos ajustes manifest si
  surgen.
- **AC**: transversal.
- **Depende de**: T6..T10.
- **Paralelizable con**: ninguna.
- **Verify**:
  6 reglas seedeadas en dev/stage/prod.
  Deploys exitosos: auth_email_worker, auth, users.
- **Done**: seeds aplicados + deploys verdes.

### T12: Verificacion E2E + ER + limpieza spec (= seccion 11)

- **Archivos**:
  - tests integration de users (~9 archivos)
  - `docs/diagrams/db-er.mmd` (modificar)
  - `docs/specs/03-auth-users-management/` (eliminar)
- **AC**: TODOS.
- **Depende de**: T2..T11.
- **Paralelizable con**: ninguna.
- **Verify**: ver [11-verificacion-e2e.md](11-verificacion-e2e.md).
- **Done**: bateria verde.

## Tabla de paralelismo

| Tarea | Depende de | Paralelizable con |
|-------|------------|--------------------|
| T1 plan + claude docs | — | — |
| T2 shared.auth.admin | T1 | T3, T4, T5 |
| T3 schema + repos | T1 | T2, T4, T5 |
| T4 SSM admin-emails | T1 | T2, T3, T5 |
| T5 auth_email_worker ext | T1 | T2, T3, T4 |
| T6 users scaffold + services | T2, T3, T4 | T5 |
| T7 controllers profile | T6 | T8, T9, T10 |
| T8 controllers status | T6 | T7, T9, T10 |
| T9 controllers admin | T2, T6 | T7, T8, T10 |
| T10 sessions tracking en auth | T3 | T7, T8, T9 |
| T11 rate-limit + deploys | T6..T10 | — |
| T12 E2E + ER + cleanup | T2..T11 | — |

## Maximo paralelismo util

- Tras T1: **4 worktrees concurrentes** (T2, T3, T4, T5).
- Tras T6: **4 worktrees concurrentes** (T7, T8, T9, T10).

8 worktrees totales a lo largo del plan, max 4 simultaneos. Dentro
del limite de 5-7 recomendado.

## Anti-patrones evitados

- T7, T8, T9 son worktree-safe entre si (cada uno su subcarpeta
  `controllers/<op>/` + su `models/<op>.py` ya cerrado en T6).
- T10 toca el lambda `auth` (distinto al `users`). NO se solapa con
  T7-T9.
- T6 (scaffold) cierra `core/models/event.py`, `core/settings/operations.py`,
  `core/models/{profile,status,admin}.py` desde el inicio. Los worktrees
  T7/T8/T9 NO los modifican (cero conflicto).
- T3 (schema) bloquea T6 (lambda users) y T10 (sessions tracking en
  auth). T2 (shared.auth.admin) bloquea T6 (depende del `require_admin`)
  y T9 (depende del `require_admin_user`).
