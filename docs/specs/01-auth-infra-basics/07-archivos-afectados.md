# 07. Archivos Afectados

> Paths relativos desde root. Cada archivo tiene su comando de
> verificacion explicito. Las secciones se ordenan por capa (schema ->
> shared -> infra -> services).

## Crear

### Migration Alembic + modelos Neon

- `serverless/lambda/shared/db/alembic/versions/00000002_auth_schema.py`
  — migracion con upgrade + downgrade idempotente para `auth_*`.
  - Verificar (en branch Neon de prueba):
    `alembic -c shared/db/alembic.ini upgrade head`
    `alembic -c shared/db/alembic.ini downgrade -1`
    `alembic -c shared/db/alembic.ini upgrade head`
  - Aplicar a dev: `serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev`
- `serverless/lambda/shared/db/models/auth/__init__.py` — re-exports.
- `serverless/lambda/shared/db/models/auth/enums.py` — `AuthUserStatus`,
  `AuthCodeKind`, `AuthLinkKind`.
- `serverless/lambda/shared/db/models/auth/user.py` — `AuthUser`.
- `serverless/lambda/shared/db/models/auth/credentials.py` — `AuthCredentials`.
- `serverless/lambda/shared/db/models/auth/email_code.py` — `AuthEmailCode`.
- `serverless/lambda/shared/db/models/auth/magic_link.py` — `AuthMagicLink`.
- `serverless/lambda/shared/db/models/auth/audit_log.py` — `AuthAuditLog`.
- `serverless/lambda/shared/db/repositories/auth.py` — helpers puros
  sobre `Session`.
  - Verificar todos los anteriores: `serverless lint-deps --shared`
    + `serverless tests --type=unit --shared` verde.

### Shared subpackage `shared.auth`

- `serverless/lambda/shared/auth/__init__.py` — re-exports + `__all__`.
- `serverless/lambda/shared/auth/pyproject.toml` — `pyjwt>=2.9`,
  `argon2-cffi>=23.1`. `internal-deps: [core, aws, observability]`.
- `serverless/lambda/shared/auth/uv.lock` — generado por `uv lock`.
- `serverless/lambda/shared/auth/constants.py` — `CODE_ALPHABET`,
  `CODE_LENGTH`, `JWT_ALGORITHM`, lifetimes.
- `serverless/lambda/shared/auth/jwt.py` — `issue_temp_jwt`,
  `issue_access_jwt`, `issue_refresh_jwt`, `verify_jwt`, `JwtClaims`,
  excepciones.
- `serverless/lambda/shared/auth/password.py` — `hash_password`,
  `verify_password`, `NeedsRehashError`.
- `serverless/lambda/shared/auth/codes.py` — `generate_code`, `hash_code`,
  `compare_code`.
- `serverless/lambda/shared/auth/tokens.py` — `generate_opaque_token`,
  `hash_token`, `compare_token`.
- `serverless/lambda/shared/tests/unit/shared/auth/test_*.py` — 17 archivos
  listados en [03-shared-auth.md](03-shared-auth.md).
  - Verificar todo lo anterior:
    `serverless lint-deps --shared`
    `serverless tests --type=unit --shared`

### Infra (resources/)

- `serverless/lambda/resources/dynamodb/jwt-blacklist.yaml` — tabla +
  GSI by_family_id, TTL=`exp`.
- `serverless/lambda/resources/dynamodb/auth-codes.yaml` — tabla,
  TTL=`expires_at`.
- `serverless/lambda/resources/sqs/auth-email-queue.yaml` — cola
  principal.
- `serverless/lambda/resources/sqs/auth-email-dlq.yaml` — DLQ.
- `serverless/lambda/resources/secrets/jwt-secret.yaml` — entrada del
  catalogo de secretos (SecureString + KMS).
  - Verificar todos los anteriores:
    `serverless validate-catalog --stage=dev`
    `serverless list-resources --stage=dev`
    `serverless provision-infra --stage=dev --aws-profile=tfs-dev`

### Lambda `auth_email_worker` (services/)

- `serverless/lambda/services/auth_email_worker/manifest.yaml`.
- `serverless/lambda/services/auth_email_worker/pyproject.toml`.
- `serverless/lambda/services/auth_email_worker/uv.lock`.
- `serverless/lambda/services/auth_email_worker/.gitignore`
  (`build/`, `build.zip`).
- `serverless/lambda/services/auth_email_worker/core/handler.py`
  (entry, `run_controller(event, EVENT_MODEL)`).
- `serverless/lambda/services/auth_email_worker/core/settings/config.py`.
- `serverless/lambda/services/auth_email_worker/core/settings/operations.py`
  (un solo operation `email`, action por `kind`).
- `serverless/lambda/services/auth_email_worker/core/models/event.py`.
- `serverless/lambda/services/auth_email_worker/core/models/email.py`
  (Pydantic schemas por kind).
- `serverless/lambda/services/auth_email_worker/core/controllers/email/`
  (un controller por kind: `RegisterMagicLink`, `RegisterCode`,
  `LoginMagicLink`, `LoginCode`, `PasswordReset`).
- `serverless/lambda/services/auth_email_worker/core/services/template_service.py`
  (renderiza Jinja2-like simple).
- `serverless/lambda/services/auth_email_worker/core/services/send_service.py`
  (wrapper de `shared.aws.send_email`).
- `serverless/lambda/services/auth_email_worker/core/services/audit_service.py`.
- `serverless/lambda/services/auth_email_worker/core/templates/{es,en}/{register-magic-link,register-code,login-magic-link,login-code,password-reset}.{txt,html}`.
- `serverless/lambda/services/auth_email_worker/events/*.json` (eventos
  SQS de prueba para `serverless run`).
- `serverless/lambda/services/auth_email_worker/tests/unit/...` (8 archivos).
  - Verificar:
    `serverless lint-deps --lambda=auth_email_worker`
    `serverless tests --type=unit --lambda=auth_email_worker`
    `serverless run --stage=local --lambda=auth_email_worker --event=events/register-magic-link.json`

### Lambda `auth` (services/)

Estructura completa listada en [05-lambda-auth-arquitectura.md](05-lambda-auth-arquitectura.md):

- `serverless/lambda/services/auth/manifest.yaml`.
- `serverless/lambda/services/auth/pyproject.toml`.
- `serverless/lambda/services/auth/uv.lock`.
- `serverless/lambda/services/auth/.gitignore`.
- `serverless/lambda/services/auth/core/handler.py`.
- `serverless/lambda/services/auth/core/settings/{config,operations}.py`.
- `serverless/lambda/services/auth/core/models/{event,register,login,verify,session}.py`.
- `serverless/lambda/services/auth/core/controllers/register/{start,verify_magic_link,verify_code}.py`.
- `serverless/lambda/services/auth/core/controllers/login/{start,verify_magic_link,verify_code}.py`.
- `serverless/lambda/services/auth/core/controllers/verify/{set_password,resend_code}.py`.
- `serverless/lambda/services/auth/core/controllers/session/{refresh,logout}.py`.
- `serverless/lambda/services/auth/core/services/{user,code,magic_link,jwt,blacklist,email_dispatch,audit,rate_limit,flow}_service.py`.
- `serverless/lambda/services/auth/events/*.json` (10 archivos: uno por action).
- `serverless/lambda/services/auth/tests/unit/...` (60+ archivos listados
  en [06-testing.md](06-testing.md)).
- `serverless/lambda/services/auth/tests/integration/...` (7 archivos).
  - Verificar:
    `serverless lint-deps --lambda=auth`
    `serverless tests --type=unit --lambda=auth`
    `serverless tests --type=coverage --lambda=auth` (>= 80% per-file)
    `serverless run --stage=local --lambda=auth --event=events/register-start.json`

### Diagrama ER (actualizacion del existente)

- `docs/diagrams/db-er.mmd` — agregar el cluster `auth_*` (5 tablas)
  + relacion `cv_profiles --o| auth_users : owns_account`.
  - Verificar: `cat docs/diagrams/db-er.mmd | head -50` muestra
    cluster nuevo.

### Documentacion permanente que sobrevive al merge

- `.claude/docs/auth-system/README.md` — overview del sistema auth
  (decisiones de arquitectura, JWT lifecycle, schema, flujos). Sirve
  como referencia tras eliminar la carpeta `docs/specs/01-auth-infra-basics/`.
- `.claude/docs/auth-system/01-jwt-lifecycle.md` — JWT temp / access /
  refresh, rotation, blacklist, family detection.
- `.claude/docs/auth-system/02-flows.md` — diagramas ASCII de cada flujo
  (register, login, verify, refresh, logout).
- `.claude/docs/auth-system/03-rate-limit-rules.md` — reglas activas.
- `.claude/rules/auth-system.md` — rule para futuras modificaciones
  (links a la skill, reglas duras, anti-patterns).
- `.claude/skills/auth-system/SKILL.md` — skill invocable
  `/auth-system` con keywords ES/EN para futuras consultas.
  - Verificar: lint + 5 prompts de validacion segun
    `.claude/rules/claude-config-testing.md`.

## Modificar

- `docs/specs/01-auth-infra-basics/` — esta carpeta del plan (efimera,
  se elimina en commit final).
- `serverless/lambda/shared/db/__init__.py` — agregar re-exports si
  los nuevos modelos requieren simbolos publicos no expuestos hoy
  (probable: ningun cambio porque los modelos se importan via
  `shared.db.models.auth`).
- `serverless/lambda/shared/db/models/__init__.py` — agregar import
  del subpaquete `auth` para que Alembic autogenerate lo detecte.
  - Verificar: `serverless tests --type=unit --shared` y migration
    autogenerate produce un diff vacio tras aplicar la migration.
- `docs/diagrams/db-er.mmd` — ya listado en "Crear" (update del archivo
  existente).

## Eliminar

(nada en este plan — todo es agregar)

## NO se toca (defensa)

- Frontend Astro (`apps/*`).
- Lambdas existentes (`cv`, `contact_form`, `tracking_pixel`,
  `contact_worker`, `tracking_worker`, `stream_processor`, `db`).
- `shared/` subpaquetes existentes (`core`, `aws`, `db` excepto el
  add-on de models/auth/, `http`, `observability`, `rate_limit`,
  `cache`, `dynamodb`, `lambda_kit`).
- `.github/workflows/*.yml` — el CI auto-detecta los nuevos
  `services/auth/` y `services/auth_email_worker/` via
  `change_detector.py`. Cero cambio en workflows.
- `docker/env/server/.*` — solo se agrega manualmente la nueva key
  `JWT_SECRET` antes del primer deploy (paso operativo, no tracked).

## Resumen contable

| Categoria | Crear | Modificar | Eliminar | Total |
|-----------|-------|-----------|----------|-------|
| Migration Alembic | 1 | 0 | 0 | 1 |
| Modelos SQLAlchemy `auth/` | 7 | 1 | 0 | 8 |
| Repository `auth` | 1 | 0 | 0 | 1 |
| `shared.auth/` (impl + tests) | 24 | 0 | 0 | 24 |
| `resources/` (dynamodb + sqs + secrets) | 5 | 0 | 0 | 5 |
| `services/auth_email_worker/` | ~25 | 0 | 0 | ~25 |
| `services/auth/` | ~80 | 0 | 0 | ~80 |
| Documentacion permanente (.claude/) | 6 | 0 | 0 | 6 |
| Plan efimero (`docs/specs/01-...`) | 12 | 0 | -12 (al cerrar) | 0 |
| Diagrama ER | 0 | 1 | 0 | 1 |
| **Total neto** |  |  |  | **~151 archivos nuevos** |
