# 09. Commits

> Rama base: `feature/auth-infra-basics` desde `dev`. PRs incrementales
> a `dev` (el usuario eligio "multiples PRs incrementales, uno por
> fase"). Conventional Commits espanol, sin atribucion de IA.

## Modelo de PRs

El usuario eligio **multiples PRs incrementales** (uno por fase del
plan). Cada PR:

- Tiene como base `dev`.
- Es atomico (cierra una fase completa, deja el repo deployable).
- Pasa el gate de la seccion 11 (lint + typecheck + tests + build).
- Se mergea con merge commit (`gh pr merge --merge --delete-branch`).

Esto da ~7-10 PRs en total (uno por tarea atomica significativa).
Algunas tareas chicas se combinan en un solo PR (T3+T4, T5+T6).

### Ramas

```text
dev
 ├── feature/auth-infra-basics-1-spec               (T1 + T13 docs base)
 ├── feature/auth-infra-basics-2-shared-auth        (T2)
 ├── feature/auth-infra-basics-3-schema-neon        (T3 + T4)
 ├── feature/auth-infra-basics-4-resources          (T5)
 ├── feature/auth-infra-basics-5-email-worker       (T6)
 ├── feature/auth-infra-basics-6-auth-scaffold      (T7 + T8)
 ├── feature/auth-infra-basics-7-register-login     (T9 + T10)
 ├── feature/auth-infra-basics-8-verify-session     (T11 + T12)
 └── feature/auth-infra-basics-9-verificacion-e2e   (T14 + limpieza)
```

Cada rama parte de `dev` actualizada (NO de la rama anterior — para
mantener PRs independientes en lo posible). Donde haya dependencia
estricta (ej. T7 necesita T2 + T3 mergeados), se espera el merge antes
de partir la siguiente rama.

## Lista completa de commits por PR

> **Recordatorio**: ANTES del primer commit verificar la rama actual.
> Si es `dev`/`stage`/`main`, crear la rama `feature/auth-infra-basics-N-<x>`
> partiendo de `dev`.

### PR 1 — `feat(specs): plan 01-auth-infra-basics`

Rama: `feature/auth-infra-basics-1-spec`.

#### Commit 1.1 — `docs(specs): plan 01-auth-infra-basics`

- Agrega `docs/specs/01-auth-infra-basics/` (12 archivos: README +
  01..11).
- Sin cambios de codigo.
- **Verificacion incremental**: `markdownlint docs/specs/01-auth-infra-basics/`
- **AC**: ninguna (meta).

#### Commit 1.2 — `docs(claude): rule + skill + docs/auth-system del sistema auth`

- Agrega `.claude/docs/auth-system/` (4 archivos).
- Agrega `.claude/rules/auth-system.md`.
- Agrega `.claude/skills/auth-system/SKILL.md`.
- **Verificacion incremental**:
  - `markdownlint .claude/docs/auth-system/ .claude/rules/auth-system.md`
  - Validacion de la skill segun `.claude/rules/claude-config-testing.md`
    (5 prompts ES con `claude --permission-mode bypassPermissions ... -p`).
- **AC**: ninguna (meta).

> Merge PR 1 a `dev` antes de PR 2.

---

### PR 2 — `feat(shared): subpackage shared.auth con JWT + argon2 + codes`

Rama: `feature/auth-infra-basics-2-shared-auth` desde `dev` (post PR 1).

#### Commit 2.1 — `feat(shared/auth): scaffold del subpackage + pyproject + constants`

- Agrega `shared/auth/__init__.py`, `pyproject.toml`, `uv.lock`,
  `constants.py`.
- `internal-deps: [core, aws, observability]`.
- Sin tests aun.
- **Verificacion incremental**:
  - `cd serverless/lambda/shared/auth && uv sync`
  - `serverless lint-deps --shared`

#### Commit 2.2 — `feat(shared/auth): jwt issue/verify temp/access/refresh`

- Implementa `shared/auth/jwt.py` con `JwtClaims`, `issue_temp_jwt`,
  `issue_access_jwt`, `issue_refresh_jwt`, `verify_jwt`, excepciones.
- Tests: `shared/tests/unit/shared/auth/test_jwt_*.py` (6 archivos).
- **Verificacion incremental**:
  `serverless tests --type=unit --shared` (los 6 nuevos verdes).
- **AC**: (transversal, soporta AC-1..AC-10).

#### Commit 2.3 — `feat(shared/auth): password hashing argon2id`

- Implementa `shared/auth/password.py`.
- Tests: `test_password_hash_verify.py`, `test_password_verify_wrong.py`,
  `test_password_needs_rehash.py`.
- **Verificacion incremental**: idem.

#### Commit 2.4 — `feat(shared/auth): generador de codes 8 chars Crockford`

- Implementa `shared/auth/codes.py` + `tokens.py`.
- Tests: 7 archivos (`test_codes_*`, `test_tokens_*`).
- **Verificacion incremental**:
  `serverless tests --type=coverage --shared` debe reportar
  `shared/auth/*.py` >= 95%.
- **AC**: (transversal).

> Merge PR 2 a `dev`.

---

### PR 3 — `feat(db): schema auth_* + models SQLAlchemy + repositories`

Rama: `feature/auth-infra-basics-3-schema-neon` desde `dev` (post PR 2).

#### Commit 3.1 — `feat(db/models): modelos SQLAlchemy del dominio auth`

- Agrega `shared/db/models/auth/__init__.py`,
  `{enums,user,credentials,email_code,magic_link,audit_log}.py`.
- Actualiza `shared/db/models/__init__.py` agregando import del
  subpaquete `auth` (necesario para Alembic autogenerate).
- **Verificacion incremental**:
  `python -m compileall -q serverless/lambda/shared/db`.
- **AC**: ninguna (base).

#### Commit 3.2 — `feat(db/alembic): migration 00000002 schema auth`

- Agrega `shared/db/alembic/versions/00000002_auth_schema.py`.
- **Verificacion incremental** (en branch Neon de prueba):
  - `neon branches create --name test-00000002 --parent main`
  - apuntar `DATABASE_URL` al branch
  - `alembic upgrade head` -> tablas creadas
  - `alembic downgrade -1` -> tablas borradas
  - `alembic upgrade head` -> recreadas (idempotente)
  - `neon branches delete test-00000002`
- **AC**: AC-15.

#### Commit 3.3 — `feat(db/repositories): helpers de auth (CRUD + audit)`

- Agrega `shared/db/repositories/auth.py` con 11 helpers.
- Agrega tests `shared/tests/unit/shared/db/repositories/test_auth_*.py`
  (~10 tests, mock de Session).
- **Verificacion incremental**: `serverless tests --type=unit --shared`
  pasa con los nuevos tests.
- **AC**: (transversal, soporta AC-1..AC-11).

#### Commit 3.4 — `chore(db): aplica migration 00000002 en dev`

- Operativo, sin cambio de codigo.
- Comando ejecutado:
  `serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev`
- Verificacion:
  `serverless run --stage=dev --lambda=db --event=events/current.json` muestra `00000002`.
- **AC**: AC-15.

> Merge PR 3 a `dev`.

---

### PR 4 — `feat(resources): DynamoDB jwt-blacklist + SQS auth-email + SSM jwt-secret`

Rama: `feature/auth-infra-basics-4-resources` desde `dev` (post PR 3).

#### Commit 4.1 — `feat(resources/dynamodb): jwt-blacklist con GSI by_family_id`

- Agrega `resources/dynamodb/jwt-blacklist.yaml` (con GSI by_family_id
  KEYS_ONLY, TTL `exp`).
- **Verificacion incremental**: `serverless validate-catalog --stage=dev`.

#### Commit 4.2 — `feat(resources/sqs): auth-email-queue + DLQ`

- Agrega `resources/sqs/auth-email-queue.yaml` y `auth-email-dlq.yaml`.
- **Verificacion incremental**: idem.

#### Commit 4.3 — `feat(resources/secrets): jwt-secret SecureString + KMS`

- Agrega `resources/secrets/jwt-secret.yaml`.
- **Verificacion incremental**: `serverless validate-catalog --stage=dev`.

#### Commit 4.4 — `chore(infra): provision dev + sync jwt-secret`

- Operativo: genera `JWT_SECRET` con `python -c "import secrets;
  print(secrets.token_urlsafe(64))"`, pega en `docker/env/server/.dev`
  (NO commiteado), sync a SSM, provisiona en AWS.
- Comandos:
  `serverless provision-infra --stage=dev --aws-profile=tfs-dev`
  `serverless sync-secrets --stage=dev --aws-profile=tfs-dev`
- Verificacion:
  `serverless secrets-status --stage=dev` reporta `SKIP` en
  `jwt-secret` (match).
  `serverless list-resources --stage=dev` muestra las 2 DDB y la cola
  + DLQ.
- **AC**: (transversal — infra).

> Merge PR 4 a `dev`.

---

### PR 5 — `feat(serverless/auth_email_worker): SQS consumer + SES sender + 5 plantillas`

Rama: `feature/auth-infra-basics-5-email-worker` desde `dev` (post PR 4).

#### Commit 5.1 — `feat(auth_email_worker): scaffold + manifest + pyproject`

- Agrega `services/auth_email_worker/{manifest.yaml,pyproject.toml,uv.lock,.gitignore}`
  + `core/{handler,settings/{config,operations}}.py` + `core/models/event.py`
  con `build_event_model({...vacio o un solo operation 'email'})`.
- **Verificacion incremental**: `python -m compileall -q`,
  `serverless lint-deps --lambda=auth_email_worker`.

#### Commit 5.2 — `feat(auth_email_worker): 5 controllers + template + send services`

- Agrega controllers: `RegisterMagicLink`, `RegisterCode`,
  `LoginMagicLink`, `LoginCode`, `PasswordReset`.
- Agrega services: `template_service.py`, `send_service.py`,
  `audit_service.py`.
- Agrega templates `{es,en}/{kind}.{txt,html}` (10 archivos).
- Agrega events JSON (5 archivos).
- Tests unit: 8 archivos (1 por escenario).
- **Verificacion incremental**:
  `serverless tests --type=unit --lambda=auth_email_worker` verde.
  `serverless run --stage=local --lambda=auth_email_worker --event=events/register-magic-link.json` exito.
- **AC**: AC-14.

#### Commit 5.3 — `chore(deploy): auth_email_worker -> dev`

- Operativo.
- Comando: `serverless deploy --lambda=auth_email_worker --stage=dev --aws-profile=tfs-dev`.
- Verificacion: `serverless status --lambda=auth_email_worker --stage=dev` -> Active.
- E2E manual: publicar un mensaje a la cola via `aws sqs send-message`
  con un kind `register-magic-link` y `to=success@simulator.amazonses.com`.
  Verificar en CloudWatch logs que el worker ejecuto y devolvio
  MessageId no vacio.

> Merge PR 5 a `dev`.

---

### PR 6 — `feat(serverless/auth): scaffold lambda + services internos`

Rama: `feature/auth-infra-basics-6-auth-scaffold` desde `dev` (post PR 5).

#### Commit 6.1 — `feat(auth): scaffold manifest + AppConfig + handler + EventModel`

- Agrega `services/auth/{manifest.yaml,pyproject.toml,uv.lock,.gitignore}`.
- `core/handler.py` con `http_handler`.
- `core/settings/{config,operations}.py`.
- `core/models/event.py` con `build_event_model(OPERATIONS)` (operations
  declaradas, controllers se agregan en commits siguientes).
- Tests minimos: 4 archivos handler/event.
- **Verificacion incremental**:
  `serverless lint-deps --lambda=auth`
  `serverless tests --type=unit --lambda=auth` (4 tests verdes).

#### Commit 6.2 — `feat(auth/services): 8 services (user/code/magic_link/jwt/blacklist/email_dispatch/audit/rate_limit/flow)`

- Implementa los 8 services + flow_service.
- Tests unit: 32 archivos.
- **Verificacion incremental**:
  `serverless tests --type=coverage --lambda=auth` cubriendo services
  con coverage >= 80%.
- **AC**: (transversal — soporta AC-1..AC-11).

#### Commit 6.3 — `feat(auth): models Pydantic + register/login/verify/session input schemas`

- Agrega `models/{register,login,verify,session}.py` (sin controllers
  todavia).
- Tests unit de validacion: 7 archivos.
- **Verificacion incremental**:
  `serverless tests --type=unit --lambda=auth`.
- **AC**: (transversal — validacion).

> Merge PR 6 a `dev`.

---

### PR 7 — `feat(auth): operations register + login (worktrees paralelos)`

Rama: `feature/auth-infra-basics-7-register-login` desde `dev` (post PR 6).

#### Commit 7.1 — `feat(auth/register): controllers start + verify-magic-link + verify-code`

- Implementa `controllers/register/{start,verify_magic_link,verify_code}.py`.
- 3 events JSON + 12 tests unit.
- **Verificacion incremental**:
  `serverless tests --type=unit --lambda=auth`
  `serverless run --stage=local --lambda=auth --event=events/register-start.json`
  responde 201 con `temp_token`.
- **AC**: AC-1, AC-2, AC-3, AC-4, AC-11, AC-12.

#### Commit 7.2 — `feat(auth/login): controllers start + verify-magic-link + verify-code`

- Implementa `controllers/login/{start,verify_magic_link,verify_code}.py`.
- 3 events JSON + 6 tests unit.
- **Verificacion incremental**: idem.
- **AC**: AC-5, AC-6.

> Merge PR 7 a `dev`.

---

### PR 8 — `feat(auth): operations verify + session + rate-limit rules seed`

Rama: `feature/auth-infra-basics-8-verify-session` desde `dev` (post PR 7).

#### Commit 8.1 — `feat(auth/verify): controllers set-password + resend-code`

- Implementa `controllers/verify/{set_password,resend_code}.py`.
- 2 events JSON + 4 tests unit.
- **Verificacion incremental**: idem.
- **AC**: AC-11 (parcial).

#### Commit 8.2 — `feat(auth/session): controllers refresh + logout`

- Implementa `controllers/session/{refresh,logout}.py`.
- 2 events JSON + 6 tests unit.
- **Verificacion incremental**: idem.
- **AC**: AC-7, AC-8, AC-9, AC-10.

#### Commit 8.3 — `chore(rate-limit): seed reglas para /auth en dev/stage/prod`

- Operativo. Inserta 5 reglas (register.start, login.start, verify.*,
  session.refresh, session.logout) via
  `serverless rate-limit set` (3 envs).
- **Verificacion incremental**:
  `serverless rate-limit list --stage=dev` muestra las 5 reglas.

#### Commit 8.4 — `chore(deploy): auth lambda -> dev/stage/prod`

- Operativo.
- Comandos:
  `serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev`
  (stage y prod se hacen tras merge a `stage` y `main` via CI).
- E2E manual en dev tras deploy: ver [11-verificacion-e2e.md](11-verificacion-e2e.md).

> Merge PR 8 a `dev`.

---

### PR 9 — `chore(specs): verificacion E2E + cierre del plan auth-infra-basics`

Rama: `feature/auth-infra-basics-9-verificacion-e2e` desde `dev`
(post PR 8). Esto es la seccion 11. Detalle en
[11-verificacion-e2e.md](11-verificacion-e2e.md).

#### Commit 9.1 — `test(auth): integration tests E2E del flujo completo`

- Agrega `services/auth/tests/integration/test_*.py` (7 archivos).
- **Verificacion incremental**:
  `serverless tests --type=integration --lambda=auth` (verde, con
  recursos AWS dev disponibles).

#### Commit 9.2 — `docs(diagrams): actualiza db-er.mmd con cluster auth_*`

- Modifica `docs/diagrams/db-er.mmd` agregando las 5 tablas + la
  relacion `cv_profiles --o| auth_users`.
- **Verificacion incremental**: render manual del .mmd OK
  (`mermaid-cli` opcional).

#### Commit 9.3 — `chore(specs): elimina la carpeta efimera del plan`

- `git rm -r docs/specs/01-auth-infra-basics/`.
- **Verificacion incremental**:
  - Bateria completa de la Parte B de la seccion 11 en verde.
  - El "Como probar" del PR usa esa bateria.
- **AC**: TODOS (consolidacion).

> Merge PR 9 a `dev`. Promociones `dev -> stage -> main` segun
> `.claude/rules/git-workflow.md`.

## Resumen de la secuencia

```text
PR 1  spec + claude docs/rule/skill            (sin codigo de prod)
PR 2  shared.auth (JWT+argon2+codes)           cubre base AC-1..AC-10
PR 3  schema Neon + repositories               cubre AC-15
PR 4  resources DynamoDB + SQS + SSM           infra
PR 5  auth_email_worker                        cubre AC-14
PR 6  auth scaffold + services                 base
PR 7  register + login                         cubre AC-1..AC-6, 11, 12
PR 8  verify + session + rate-limit seed       cubre AC-7..AC-13
PR 9  E2E integration + ER + limpieza spec     consolida
```

## PRs body — template

Cada PR sigue `.claude/rules/git-workflow.md`:

```markdown
## Problema

<1-3 bullets explicando el subscope del plan auth-infra-basics que
este PR resuelve.>

## Solucion

<numerada paralela a Problema>

## Como probar

```bash
# Bateria especifica del PR
<comandos del bloque "Verificacion incremental" de los commits>
```

## TODO

<vacio o pendientes que escapan del scope del PR pero no afectan>
```

NUNCA atribucion de IA. Lenguaje espanol. Body en `gh pr create` via
HEREDOC.
