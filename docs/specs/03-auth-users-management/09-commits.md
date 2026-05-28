# 09. Commits — plan 03

> Rama base: `feature/auth-users-management-N-<x>` desde `dev` (planes
> 01 + 02 ya mergeados). Multiples PRs incrementales.

## Ramas

```text
dev (post planes 01 + 02)
 ├── feature/auth-users-mgmt-1-spec-and-docs           (T1)
 ├── feature/auth-users-mgmt-2-shared-admin            (T2)
 ├── feature/auth-users-mgmt-3-schema-and-repos        (T3)
 ├── feature/auth-users-mgmt-4-infra                   (T4)
 ├── feature/auth-users-mgmt-5-email-worker-ext        (T5)
 ├── feature/auth-users-mgmt-6-users-scaffold          (T6)
 ├── feature/auth-users-mgmt-7a-profile-controllers    (T7 — WT-A)
 ├── feature/auth-users-mgmt-7b-status-controllers     (T8 — WT-B)
 ├── feature/auth-users-mgmt-7c-admin-controllers      (T9 — WT-C)
 ├── feature/auth-users-mgmt-8-sessions-tracking-auth  (T10 — WT-D)
 └── feature/auth-users-mgmt-9-verificacion-e2e        (T11 + T12)
```

## PR 1 — `docs(specs+claude): plan 03-auth-users-management + claude docs/auth-system users + admin + sessions`

### Commit 1.1 — `docs(specs): plan 03-auth-users-management`

- Agrega `docs/specs/03-auth-users-management/` (12 archivos).
- **Verificacion**: markdownlint.

### Commit 1.2 — `docs(claude): auth-system 06-users + 07-admin + 08-sessions + rule + skill keywords`

- Agrega 3 docs nuevos.
- Modifica `.claude/rules/auth-system.md`.
- Modifica `.claude/skills/auth-system/SKILL.md` (keywords).
- **Verificacion**:
  - markdownlint
  - 5 prompts ES via `claude -p`.

> Merge PR 1.

---

## PR 2 — `feat(shared/auth): admin whitelist via SSM`

### Commit 2.1 — `feat(shared/auth): admin.py + load_admin_emails + is_admin + require_admin`

- Agrega `shared/auth/admin.py`.
- Modifica `shared/auth/__init__.py`.
- Agrega 11 tests.
- **Verificacion**:
  - `serverless lint-deps --shared`
  - `serverless tests --type=unit --shared`

> Merge PR 2.

---

## PR 3 — `feat(db): schema auth_users extension + sessions/admin_actions/consent_log + repos`

### Commit 3.1 — `feat(db/models): auth_users extension + 3 tablas nuevas`

- Modifica `models/auth/user.py` (columnas nuevas + indices).
- Modifica `models/auth/enums.py` (AuthLinkKind: agregar `email-change`).
- Agrega `models/auth/{user_session,admin_action,consent_log}.py`.
- Modifica `models/auth/__init__.py`.
- **Verificacion**: `python -m compileall -q`.

### Commit 3.2 — `feat(db/alembic): migration 00000004_auth_users_extension`

- Agrega migration.
- **Verificacion**: branch Neon de prueba up -> down -> up
  idempotente. AC-25.

### Commit 3.3 — `feat(db/repositories): auth_users helpers + sessions + admin_actions + consent`

- Agrega `repositories/auth_users.py` (15+ helpers).
- Agrega 13 tests.
- **Verificacion**: `serverless tests --type=unit --shared`.

### Commit 3.4 — `chore(db): aplica migration 00000004 en dev`

- Operativo.
- Verificacion: `current.json` muestra `00000004`.

> Merge PR 3.

---

## PR 4 — `feat(infra): SSM admin-emails`

### Commit 4.1 — `feat(resources/secrets): admin-emails entry`

- Agrega `resources/secrets/admin-emails.yaml`.
- **Verificacion**: `serverless validate-catalog`.

### Commit 4.2 — `chore(infra): provision SSM admin-emails + sync valor en dev`

- Operativo:
  - Agregar `ADMIN_EMAILS=pacg1991@gmail.com` a `docker/env/server/.{dev,stage,prod}`.
  - `serverless provision-infra --stage=dev --aws-profile=tfs-dev`
  - `serverless sync-secrets --stage=dev --aws-profile=tfs-dev` (luego stage + prod)
- **Verificacion**: `serverless secrets-status --stage=dev` reporta
  `SKIP` en admin-emails.

> Merge PR 4.

---

## PR 5 — `feat(auth_email_worker): 3 plantillas nuevas (email-changed, account-disabled, account-deleted)`

### Commit 5.1 — `feat(auth_email_worker): 3 controllers + 3 schemas + 12 templates`

- Agrega controllers + templates es/en.
- Modifica operations.py + email.py models.
- Agrega 3 tests unit.
- **Verificacion**:
  `serverless tests --type=unit --lambda=auth_email_worker`
  `serverless run --stage=local --lambda=auth_email_worker --event=events/email-changed.json` exitoso.

### Commit 5.2 — `chore(deploy): auth_email_worker -> dev`

- Operativo: `serverless deploy --lambda=auth_email_worker --stage=dev --aws-profile=tfs-dev`.

> Merge PR 5.

---

## PR 6 — `feat(users): scaffold lambda + services internos + EventModel`

### Commit 6.1 — `feat(users): scaffold manifest + AppConfig + handler`

- Agrega `services/users/{manifest.yaml, pyproject.toml, uv.lock, .gitignore, core/handler.py, core/settings/{config,operations}.py, core/models/event.py}`.
- **Verificacion**:
  `serverless lint-deps --lambda=users`
  `python -m compileall -q services/users`

### Commit 6.2 — `feat(users/services): 10 services internos + tests`

- Agrega `core/services/*.py` (10).
- Agrega ~25 tests.
- **Verificacion**: `serverless tests --type=coverage --lambda=users` (>= 80% en services).

### Commit 6.3 — `feat(users/models): Pydantic schemas + tests`

- Agrega `core/models/{profile,status,admin}.py`.
- Modifica `event.py` agregando los 14 actions.
- Agrega ~10 tests models.
- **Verificacion**: `serverless tests --type=unit --lambda=users`.

> Merge PR 6.

---

## PR 7a — `feat(users/profile): controllers profile (4 actions)`

Rama: `feature/auth-users-mgmt-7a-profile-controllers` (worktree
WT-A). Disjunto de PR 7b y PR 7c — mergear en cualquier orden.

### Commit 7a.1 — `feat(users/profile): 4 controllers + 10 tests`

- Agrega `controllers/profile/{get,update,change_email,delete_account}.py`.
- Agrega 4 events JSON + 10 tests.
- **AC**: AC-1..AC-6, AC-26, AC-29 (guard self-delete admin).
- **Verificacion**: `serverless tests --type=unit --lambda=users`.

> Merge PR 7a a `dev`.

---

## PR 7b — `feat(users/status): controllers status (3 actions)`

Rama: `feature/auth-users-mgmt-7b-status-controllers` (worktree
WT-B). Disjunto de PR 7a y PR 7c.

### Commit 7b.1 — `feat(users/status): 3 controllers + 4 tests`

- Agrega `controllers/status/{get,list_sessions,revoke_session}.py`.
- Agrega 3 events JSON + 4 tests.
- **AC**: AC-7..AC-10.
- **Verificacion**: `serverless tests --type=unit --lambda=users`.

> Merge PR 7b a `dev`.

---

## PR 7c — `feat(users/admin): controllers admin (7 actions)`

Rama: `feature/auth-users-mgmt-7c-admin-controllers` (worktree
WT-C). Disjunto de PR 7a y PR 7b.

### Commit 7c.1 — `feat(users/admin): 7 controllers + 13 tests`

- Agrega
  `controllers/admin/{list_users,get_user,disable_user,enable_user,force_logout,delete_user,list_admin_actions}.py`.
- Agrega 7 events JSON + 13 tests.
- **AC**: AC-11..AC-21, AC-28.
- **Verificacion**: `serverless tests --type=unit --lambda=users`.

> Merge PR 7c a `dev`.
>
> **Por que 3 PRs en vez de 1**: cumple
> [git-workflow.md](../../../.claude/rules/git-workflow.md) ("PRs
> pequenos y atomicos"). Los 3 worktrees son disjuntos en su zona
> de write (subcarpetas `controllers/<op>/` + events `<op>-*.json` +
> tests por op) — `event.py` y `models/{profile,status,admin}.py`
> ya estan cerrados en PR 6. El review humano de 4-7 controllers
> por PR es manejable, en cambio uno solo de 14 es ruido.

---

## PR 8 — `feat(auth): sessions tracking integrado en el lambda auth`

### Commit 8.1 — `feat(auth/services): session_tracking_service helper`

- Agrega `services/session_tracking_service.py`.
- Agrega tests unit del helper.
- **Verificacion**: `serverless tests --type=unit --lambda=auth` (no
  regresiones).

### Commit 8.2 — `feat(auth/controllers): inyecta session_tracking en verify-* + refresh + logout`

- Modifica 8 controllers (verify_magic_link x2, verify_code x2,
  verify_password, verify_totp, webauthn.login_verify, mfa.recovery_codes_consume, session.refresh, session.logout).
- Cada modificacion es minima: 2-3 lineas para llamar al helper.
- **Verificacion**:
  `serverless tests --type=unit --lambda=auth` verde
  `serverless run --stage=local --lambda=auth --event=events/session-refresh.json` rotation funciona

### Commit 8.3 — `test(auth): integration tests session tracking E2E`

- Agrega 4 integration tests en `services/auth/tests/integration/`.
- **AC**: AC-22, AC-23, AC-24.
- **Verificacion**:
  `serverless tests --type=integration --lambda=auth` (con AWS dev).

### Commit 8.4 — `chore(deploy): auth lambda con session tracking -> dev`

- Operativo: `serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev`.

> Merge PR 8.

---

## PR 9 — `chore: rate-limit seed + deploy users + verificacion E2E + cleanup spec 03`

### Commit 9.1 — `chore(rate-limit): seed reglas users# en dev/stage/prod`

- Operativo. 6 reglas (profile.get, profile.update, profile.change-email,
  profile.delete-account, status, admin).

### Commit 9.2 — `chore(deploy): users lambda -> dev`

- Operativo: `serverless deploy --lambda=users --stage=dev --aws-profile=tfs-dev`.
- Verificacion: `serverless status --lambda=users --stage=dev` -> Active.

### Commit 9.3 — `test(users): 9 integration tests E2E`

- Agrega tests integration en `services/users/tests/integration/`.
- **Verificacion**: `serverless tests --type=integration --lambda=users`.

### Commit 9.4 — `docs(diagrams): actualiza db-er.mmd con auth_user_sessions + admin_actions + consent_log`

- Modifica `docs/diagrams/db-er.mmd`.

### Commit 9.5 — `chore(specs): elimina la carpeta efimera del plan 03`

- `git rm -r docs/specs/03-auth-users-management/`.
- **Verificacion**: bateria de [11-verificacion-e2e.md](11-verificacion-e2e.md) en verde.

> Merge PR 9 a `dev`. Promociones a `stage` y `main`.

## Resumen de la secuencia

```text
PR 1  spec + docs/claude                       (sin codigo)
PR 2  shared.auth.admin                        AC-11, AC-21
PR 3  schema + repos                           AC-25
PR 4  SSM admin-emails                         infra
PR 5  auth_email_worker plantillas             notifications
PR 6  users scaffold + services + models       transversal
PR 7a controllers profile                      AC-1..6, AC-26, AC-29
PR 7b controllers status                       AC-7..10
PR 7c controllers admin                        AC-11..21, AC-28
PR 8  sessions tracking en auth                AC-22..24
PR 9  deploy + integration + ER + cleanup      consolida
```

## PR body template — sin atribucion IA

Cada PR usa `.claude/rules/git-workflow.md`: Problema / Solucion / Como
probar / TODO.
