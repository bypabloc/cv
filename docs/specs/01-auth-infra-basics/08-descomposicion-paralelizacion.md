# 08. Descomposicion para Paralelizacion

> Plan **Large** (~151 archivos). 14 tareas atomicas. Limite practico
> 5-7 worktrees concurrentes. Las tareas pasan los 3 checks (File
> Exclusivity, Interface Stability, Bounded Scope).

## Grafo de dependencias (alto nivel)

```text
T1 plan                                  (raiz, sin codigo)
  |
  +--> T2 shared.auth subpackage         (raiz tras T1)
  |
  +--> T3 schema Neon + models           (raiz tras T1, indep de T2)
  |     |
  |     +--> T4 repository helpers
  |
  +--> T5 resources (ddb + sqs + ssm)    (raiz tras T1, indep de T2/T3)
  |
  +--> T6 auth_email_worker              (depende de T5 sqs)
  |
  +--> T7 auth scaffold (manifest+config+handler+EventModel)
  |     | depende de: T2 (jwt/codes), T3 (models), T4 (repositories), T5 (tables/queues)
  |     |
  |     +--> T8 services (user, code, magic_link, jwt, blacklist, email_dispatch, audit, rate_limit, flow)
  |     |
  |     +--> T9 operation register (3 controllers + models)        (paralelo con T10, T11, T12)
  |     +--> T10 operation login (3 controllers + models)          (paralelo con T9, T11, T12)
  |     +--> T11 operation verify (2 controllers + models)         (paralelo con T9, T10, T12)
  |     +--> T12 operation session (2 controllers + models)        (paralelo con T9, T10, T11)
  |
  +--> T13 documentacion permanente (.claude/docs/auth-system/, rule, skill)
  |     paralelo con todo lo anterior tras T1
  |
  +--> T14 verificacion E2E + actualizacion ER + limpieza spec     (seccion 11; SIEMPRE ultimo)
```

## Tareas (orden topologico)

### T1: Plan (carpeta `docs/specs/01-auth-infra-basics/`)

- **Archivos**: `docs/specs/01-auth-infra-basics/*.md` (12 archivos, este plan).
- **AC referenciados**: ninguna (meta).
- **Depende de**: ninguna.
- **Paralelizable con**: ninguna (raiz, base).
- **Verify**: `markdownlint docs/specs/01-auth-infra-basics/*.md` sin errores.
- **Done**: carpeta commiteada en `feature/auth-infra-basics`.

### T2: Shared subpackage `shared.auth`

- **Archivos**:
  - `serverless/lambda/shared/auth/__init__.py`
  - `serverless/lambda/shared/auth/pyproject.toml`
  - `serverless/lambda/shared/auth/uv.lock`
  - `serverless/lambda/shared/auth/{constants,jwt,password,codes,tokens}.py`
  - `serverless/lambda/shared/tests/unit/shared/auth/test_*.py` (17 archivos)
- **AC referenciados**: (transversal, soporta AC-1..AC-10)
- **Depende de**: T1.
- **Paralelizable con**: T3, T5, T13.
- **Verify**:
  `serverless lint-deps --shared`
  `serverless tests --type=unit --shared` (incluye los 17 tests nuevos)
- **Done**: 17 tests verdes, coverage `shared/auth/` >= 95%,
  `lint-deps` reporta el cierre transitivo de auth (sin duplicados).

### T3: Schema Neon (migration + modelos)

- **Archivos**:
  - `serverless/lambda/shared/db/alembic/versions/00000002_auth_schema.py`
  - `serverless/lambda/shared/db/models/auth/__init__.py`
  - `serverless/lambda/shared/db/models/auth/{enums,user,credentials,email_code,magic_link,audit_log}.py`
  - `serverless/lambda/shared/db/models/__init__.py` (1 linea agregada)
- **AC referenciados**: AC-15 (downgrade up idempotente).
- **Depende de**: T1.
- **Paralelizable con**: T2, T5, T13.
- **Verify**:
  - `python -m compileall -q serverless/lambda/shared/db`
  - En branch Neon de prueba: `alembic upgrade head` -> `downgrade -1`
    -> `upgrade head`. Cero diff con `alembic check`.
  - `serverless tests --type=unit --shared` verde.
- **Done**: migration aplica + reverte sin error; 5 tablas creadas con
  las columnas/indices del archivo 02; FK a `cv_profiles` valida.

### T4: Repository helpers `shared.db.repositories.auth`

- **Archivos**: `serverless/lambda/shared/db/repositories/auth.py` +
  tests `shared/tests/unit/shared/db/repositories/test_auth_*.py`
  (~10 tests).
- **AC referenciados**: soporta AC-1..AC-11.
- **Depende de**: T3.
- **Paralelizable con**: T2 (paquetes diferentes), T5, T13.
- **Verify**:
  `serverless tests --type=unit --shared` cubriendo los nuevos tests
  (con DB en memoria via SQLAlchemy `:memory:` o mock de Session).
- **Done**: 11 helpers implementados, tests verdes.

### T5: Resources (DynamoDB + SQS + SSM)

- **Archivos**:
  - `serverless/lambda/resources/dynamodb/jwt-blacklist.yaml`
  - `serverless/lambda/resources/dynamodb/auth-codes.yaml`
  - `serverless/lambda/resources/sqs/auth-email-queue.yaml`
  - `serverless/lambda/resources/sqs/auth-email-dlq.yaml`
  - `serverless/lambda/resources/secrets/jwt-secret.yaml`
- **AC referenciados**: (transversal — infra)
- **Depende de**: T1.
- **Paralelizable con**: T2, T3, T13.
- **Verify**:
  `serverless validate-catalog --stage=dev`
  `serverless provision-infra --stage=dev --aws-profile=tfs-dev`
  `serverless list-resources --stage=dev` muestra los 5 nuevos.
- **Done**: las 2 DDB tables + GSI + SQS + DLQ + SSM publicados en
  AWS dev. SSM paths
  `/portfolio/dev/dynamodb/{jwt-blacklist,auth-codes}/name`
  resolvibles. Cola DLQ asociada con `redrive_policy`.

### T6: Lambda `auth_email_worker`

- **Archivos**: ~25 (manifest + pyproject + handler + 5 controllers +
  3 services + 10 templates + tests + events).
- **AC referenciados**: AC-14.
- **Depende de**: T1, T5 (cola). NO depende de T2/T3 (worker no usa
  shared.auth ni el schema auth; solo dispara SES).
- **Paralelizable con**: T7+ tras T5 lista.
- **Verify**:
  `serverless lint-deps --lambda=auth_email_worker`
  `serverless tests --type=unit --lambda=auth_email_worker` (8 tests)
  `serverless run --stage=local --lambda=auth_email_worker --event=events/register-magic-link.json` (SES mock o sandbox)
  `serverless deploy --lambda=auth_email_worker --stage=dev --aws-profile=tfs-dev`
- **Done**: tests verdes, deploy OK, primer mensaje E2E enviado a
  SES sandbox (`success@simulator.amazonses.com`).

### T7: Lambda `auth` — scaffold

- **Archivos**:
  - `serverless/lambda/services/auth/manifest.yaml`
  - `serverless/lambda/services/auth/pyproject.toml`
  - `serverless/lambda/services/auth/uv.lock`
  - `serverless/lambda/services/auth/.gitignore`
  - `serverless/lambda/services/auth/core/handler.py`
  - `serverless/lambda/services/auth/core/settings/{config,operations}.py`
  - `serverless/lambda/services/auth/core/models/event.py` (placeholder
    con build_event_model({}) -> se llena en T9-T12)
- **AC referenciados**: ninguna (scaffold).
- **Depende de**: T2, T3, T4, T5.
- **Paralelizable con**: T6, T13 si ya completados los predecesores.
- **Verify**:
  `python -m compileall -q serverless/lambda/services/auth`
  `serverless lint-deps --lambda=auth`
  `serverless tests --type=unit --lambda=auth` (handler tests minimos)
- **Done**: el lambda compila, `serverless run` con event vacio
  responde 404 (sin operations registrados aun).

### T8: Services del Lambda auth (8 services)

- **Archivos**:
  - `serverless/lambda/services/auth/core/services/{user,code,magic_link,jwt,blacklist,email_dispatch,audit,rate_limit,flow}_service.py`
  - `serverless/lambda/services/auth/tests/unit/services/test_*.py` (~32 tests)
- **AC referenciados**: transversal.
- **Depende de**: T7.
- **Paralelizable con**: T9, T10, T11, T12 (los controllers consumen
  estos services; pero a nivel files NO se solapan — los services
  son archivos propios). Decision: ejecutar T8 ANTES de T9-T12 para
  reducir merge churn (controllers terminan importando estos modulos).
- **Verify**:
  `serverless tests --type=unit --lambda=auth` (los services verdes;
  controllers no existen aun).
- **Done**: 8 services implementados, 32 tests verdes, coverage >= 80%.

### T9: Operation `register` (paralelizable con T10, T11, T12)

- **Archivos**:
  - `serverless/lambda/services/auth/core/models/register.py`
  - `serverless/lambda/services/auth/core/controllers/register/{__init__,start,verify_magic_link,verify_code}.py`
  - `serverless/lambda/services/auth/tests/unit/controllers/test_register_*.py` (~12 tests)
  - `serverless/lambda/services/auth/events/register-*.json` (3 archivos)
- **AC referenciados**: AC-1, AC-2, AC-3, AC-4, AC-11, AC-12.
- **Depende de**: T7, T8.
- **Paralelizable con**: T10, T11, T12 (archivos disjuntos).
- **Verify**:
  `serverless tests --type=unit --lambda=auth` cubriendo los 12 tests
  `serverless run --stage=local --lambda=auth --event=events/register-start.json`
- **Done**: 3 controllers verdes, 12 tests verdes, run local devuelve
  201 con temp_token.

### T10: Operation `login` (paralelizable con T9, T11, T12)

- **Archivos**:
  - `serverless/lambda/services/auth/core/models/login.py`
  - `serverless/lambda/services/auth/core/controllers/login/{__init__,start,verify_magic_link,verify_code}.py`
  - `serverless/lambda/services/auth/tests/unit/controllers/test_login_*.py` (~6 tests)
  - `serverless/lambda/services/auth/events/login-*.json` (3 archivos)
- **AC referenciados**: AC-5, AC-6.
- **Depende de**: T7, T8.
- **Paralelizable con**: T9, T11, T12.
- **Verify**: idem T9.
- **Done**: idem T9 para login.

### T11: Operation `verify` (paralelizable con T9, T10, T12)

- **Archivos**:
  - `serverless/lambda/services/auth/core/models/verify.py`
  - `serverless/lambda/services/auth/core/controllers/verify/{__init__,set_password,resend_code}.py`
  - `serverless/lambda/services/auth/tests/unit/controllers/test_verify_*.py` (~4 tests)
  - `serverless/lambda/services/auth/events/verify-*.json` (2 archivos)
- **AC referenciados**: AC-11 (parcial).
- **Depende de**: T7, T8.
- **Paralelizable con**: T9, T10, T12.
- **Verify**: idem.
- **Done**: 2 controllers, 4 tests verdes.

### T12: Operation `session` (paralelizable con T9, T10, T11)

- **Archivos**:
  - `serverless/lambda/services/auth/core/models/session.py`
  - `serverless/lambda/services/auth/core/controllers/session/{__init__,refresh,logout}.py`
  - `serverless/lambda/services/auth/tests/unit/controllers/test_session_*.py` (~6 tests)
  - `serverless/lambda/services/auth/events/session-*.json` (2 archivos)
- **AC referenciados**: AC-7, AC-8, AC-9, AC-10.
- **Depende de**: T7, T8.
- **Paralelizable con**: T9, T10, T11.
- **Verify**: idem.
- **Done**: 2 controllers, 6 tests verdes.

### T13: Documentacion permanente

- **Archivos**:
  - `.claude/docs/auth-system/README.md`
  - `.claude/docs/auth-system/01-jwt-lifecycle.md`
  - `.claude/docs/auth-system/02-flows.md`
  - `.claude/docs/auth-system/03-rate-limit-rules.md`
  - `.claude/rules/auth-system.md`
  - `.claude/skills/auth-system/SKILL.md`
- **AC referenciados**: ninguna (meta-documentacion).
- **Depende de**: T1 (visibilidad), idealmente T2/T3 cerrados para
  documentar la interfaz real.
- **Paralelizable con**: T2-T12 (archivos disjuntos del codigo).
- **Verify**:
  `markdownlint .claude/docs/auth-system/*.md .claude/rules/auth-system.md`
  `claude --permission-mode bypassPermissions ... -p "como funciona el flujo de magic link"`
  (debe activar la skill, num_turns > 1)
- **Done**: 5 prompts de validacion pasan, link checks OK.

### T14: Verificacion E2E + actualizacion ER + limpieza spec (= seccion 11)

- **Archivos**:
  - `docs/diagrams/db-er.mmd` (actualizar)
  - `docs/specs/01-auth-infra-basics/` (eliminar con `git rm -r`)
  - Posibles ajustes finales tras integrar todo.
- **AC referenciados**: TODOS (verificacion consolidada).
- **Depende de**: T2..T13 todos completos.
- **Paralelizable con**: ninguna (es el cierre).
- **Verify**: ver [11-verificacion-e2e.md](11-verificacion-e2e.md).
- **Done**: bateria E2E verde, ER actualizado, spec borrada.

## Tabla resumen de paralelismo

| Tarea | Depende de | Paralelizable con |
|-------|------------|--------------------|
| T1  plan                | —                 | — |
| T2  shared.auth          | T1                | T3, T5, T13 |
| T3  schema Neon          | T1                | T2, T5, T13 |
| T4  repository auth      | T3                | T2, T5, T13 |
| T5  resources            | T1                | T2, T3, T13 |
| T6  auth_email_worker    | T5                | T7+ tras T2/T3/T4/T5 |
| T7  auth scaffold        | T2, T3, T4, T5    | T6, T13 |
| T8  auth services        | T7                | T13 |
| T9  register             | T7, T8            | T10, T11, T12, T13 |
| T10 login                | T7, T8            | T9, T11, T12, T13 |
| T11 verify               | T7, T8            | T9, T10, T12, T13 |
| T12 session              | T7, T8            | T9, T10, T11, T13 |
| T13 docs permanentes     | T1                | T2..T12 |
| T14 verificacion E2E     | T2..T13           | — |

## Maximo paralelismo util

- Tras T1: lanzar **T2 + T3 + T5 + T13** en 4 worktrees (raices,
  archivos disjuntos).
- Tras T7+T8: lanzar **T9 + T10 + T11 + T12** en 4 worktrees
  (operaciones disjuntas).
- T6 puede correr tan pronto T5 este lista (puede solaparse con T7
  scaffold).

Recomendacion practica: 4 worktrees concurrentes maximo. Pasa los 3
checks por construccion.

## Anti-patrones evitados

- T9, T10, T11, T12 tocan archivos disjuntos (cada una su carpeta
  `controllers/<op>/` + su `models/<op>.py` + tests propios). File
  Exclusivity OK.
- T8 services se completa ANTES de T9-T12 para que los controllers
  no inventen interfaces (Interface Stability OK).
- T14 verificacion E2E NO se paraleliza — toca archivos transversales
  (ER diagram, ajustes finales) y consolida todo.
- Las tareas T9-T12 NO modifican `core/models/event.py` (lo crea T7
  con el dict de OPERATIONS completo desde el inicio). Cada operation
  ya esta registrada en el scaffold, solo no tiene controllers (que
  aparecen al integrar).
