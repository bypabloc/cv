# Plan d-shared-only-imports

> Estandar duro: los `serverless/lambda/services/*/core/**/*.py` NO importan
> directamente paquetes externos. Toda dependencia externa (pydantic,
> sqlalchemy, alembic, psycopg, boto3, aws-lambda-powertools) viaja por
> `serverless/lambda/shared/**`. Cada subpaquete shared es el portador unico
> de su paquete y lo re-exporta. `serverless lint-deps` valida el contrato.

## Contexto

Auditoria del backend (mayo 2026) detecto 14 imports directos a paquetes
prohibidos en `services/*/core/`:

| Paquete | Archivos consumers en services | Portador shared |
|---------|--------------------------------|-----------------|
| `pydantic` | 5 (cv, db, contact_form, tracking_pixel, stream_processor — todos en `core/models/*.py`) | `shared.core` (declarado, NO re-exporta) |
| `pydantic[email]` | 1 (contact_form/core/models/contact.py — `EmailStr`) | NINGUNO (declarado solo en contact_form, EXCEPTION D-3) |
| `boto3` | 2 (contact_form/core/services/contact_service.py, stream_processor/core/services/stream_service.py) | `shared.aws`, `shared.dynamodb`, `shared.cache` |
| `sqlalchemy` | 1 (db/core/services/seed_service.py — `select`, `func`, `insert.on_conflict_do_update`, `Session`) | `shared.db` (declarado, NO re-exporta) |
| `aws_lambda_powertools` | 5 (cv, db, contact_form, tracking_pixel, stream_processor — `MetricUnit` en handlers/services) | `shared.aws`, `shared.observability` |
| `alembic` | 0 | `shared.db` |
| `psycopg` | 0 | `shared.db` |

El cierre transitivo de `shared/` ya aporta esos paquetes a cada Lambda
(via `internal-deps`), pero hoy:

1. `shared.core.__init__` NO re-exporta `BaseModel`, `Field`, etc.
2. `shared.db.__init__` NO re-exporta `select`, `insert`, `Session`, `func`.
3. `shared.observability.__init__` NO re-exporta `MetricUnit`.
4. `shared.aws.ses` expone solo el cliente `ses` (singleton), no helpers.
5. `serverless lint-deps` valida deps duplicadas en pyproject pero NO escanea
   imports en codigo.

Resultado: los services compilan, pero el contrato "todo via shared" es solo
documental — un import directo a `pydantic` o `boto3` pasa CI sin alertar.

## Solucion

Refactor en 7 fases atomicas:

| Fase | Archivo | Que hace |
|------|---------|----------|
| **A** | `01-fase-a-shared-core-pydantic.md` | shared.core re-exporta pydantic + mover `pydantic[email]` a shared.core |
| **B** | `02-fase-b-shared-db-sqlalchemy.md` | shared.db re-exporta `select`, `insert`, `Session`, `func` |
| **C** | `03-fase-c-shared-aws-ses-dynamodb.md` | shared.aws.ses crece a `send_email(...)`; shared.aws.dynamodb_types nuevo con `TypeDeserializer` |
| **D** | `04-fase-d-shared-observability-metricunit.md` | shared.observability re-exporta `MetricUnit` |
| **E** | `05-fase-e-migrar-services.md` | Migrar imports de los 5 services para usar shared (cero `from pydantic`, `from sqlalchemy`, `import boto3`, `from aws_lambda_powertools` en `core/`) |
| **F** | `06-fase-f-lint-deps-imports.md` | Extender `serverless lint-deps` con check de imports directos prohibidos (allowlist vacia en `core/`, tests/ exentos) |
| **G** | `07-fase-g-claude-rule-skill-docs.md` | Rule + skill + docs en `.claude/` que estandarizan el contrato para Lambdas nuevos/existentes |
| **VERIF** | `08-verificacion-e2e.md` | Bateria E2E final + eliminacion de `docs/specs/d-shared-only-imports/` |

## Decisiones (no reabribles)

1. **Pydantic via shared.core re-export**: imports cambian a `from shared.core
   import BaseModel, Field, EmailStr, field_validator`. NO existira ningun
   `from pydantic` en `core/` de un service.
2. **pydantic[email] en shared.core**: `email-validator` se carga en TODAS las
   Lambdas (peso ~150 KB en el zip). Trade-off aceptado para tener un solo
   portador. contact_form retira `pydantic[email]` de su pyproject.toml.
3. **SQLAlchemy via shared.db re-export**: `select`, `insert` (postgresql),
   `Session`, `func`. El subset es el minimo que usa el seeder hoy. Si en el
   futuro otro service necesita `update` o `delete`, se agregan al re-export.
4. **boto3 via wrappers acotados**: `shared.aws.ses.send_email(...)` (no
   exponer el cliente boto3 directo), `shared.aws.dynamodb_types.TypeDeserializer`
   (re-export limpio). Cero `import boto3` en `core/`.
5. **MetricUnit via shared.observability**: `from shared.observability import
   MetricUnit`. Mantiene el enum, evita strings magicos.
6. **Cero exenciones en `core/`**: TODO archivo `services/*/core/**/*.py` debe
   importar solo desde `shared.*`. tests/ exentos del check (pueden importar
   mocks de pydantic/boto3 si lo necesitan).
7. **Enforcement via lint-deps extendido**: NO comando nuevo. NO hook
   pre-commit. `serverless lint-deps` cubre los dos checks (deps duplicadas +
   imports prohibidos). CI ya corre el comando antes del deploy.
8. **Cliente SES en contact_form**: hoy hace `boto3.client('sesv2')` inline en
   `contact_service.py` (no usa el singleton `shared.aws.ses.ses`). El refactor
   le agrega a `shared.aws.ses` una funcion `send_email(...)` que encapsula el
   patron y contact_form la usa.
9. **Plan efimero**: la carpeta `docs/specs/d-shared-only-imports/` se elimina
   en el ultimo commit (verificacion E2E). La rule + skill + docs de Fase G
   son los artefactos permanentes que sobreviven.

## Estado por fase

| Fase | Estado | Commits estimados |
|------|--------|------------------|
| A — shared.core re-exporta pydantic | pendiente | 1 |
| B — shared.db re-exporta SQLAlchemy | pendiente | 1 |
| C — shared.aws.ses + dynamodb_types | pendiente | 1 |
| D — shared.observability re-exporta MetricUnit | pendiente | 1 |
| E — migrar services (5 services) | pendiente | 5 (1 por service) |
| F — extender lint-deps con check de imports | pendiente | 1 |
| G — rule + skill + docs en .claude/ | pendiente | 1 |
| Verificacion E2E + eliminacion del plan | pendiente | 1 |

Total estimado: **12 commits** en `feature/shared-only-imports` desde `dev`.

## Reglas criticas

- SIEMPRE editar primero el `__init__.py` del shared portador, luego migrar
  el service consumer (Fases A-D antes que E).
- SIEMPRE correr `serverless tests --type=unit --lambda=<X>` despues de
  migrar imports de un service.
- SIEMPRE correr `serverless lint-deps` despues de cada fase.
- NUNCA mezclar dos fases en un commit (cada fase = commit atomico).
- NUNCA dejar un import directo a un prohibido en `core/` despues de Fase E.
- NUNCA atribuir a IA en commits/PRs (politica de empresa).
- NUNCA `git push` sin que la bateria de verificacion (`08-verificacion-e2e.md`)
  este en verde completa.

## Matriz de verificacion

| Comando | Cuando |
|---------|--------|
| `python -m compileall -q serverless/lambda/shared/<X>` | Tras editar un `__init__.py` shared |
| `python devtools/run.py serverless tests --type=unit --lambda=<X>` | Tras migrar imports de un service |
| `python devtools/run.py serverless lint-deps` | Tras cada fase (A-G) |
| `python devtools/run.py serverless tests --shared` | Tras Fase F (validar el check nuevo) |
| `python devtools/run.py serverless tests --type=unit` | Bateria completa (Fase verif) |
| `python devtools/run.py serverless deploy --lambda=db --stage=dev` | Validar deploy real con shared re-exports (Fase verif) |
| `python devtools/run.py serverless run --stage=dev --lambda=db --event=events/seed.json` | Validar seeder con SQLAlchemy via shared (Fase verif) |

## Navegacion

- [01-fase-a-shared-core-pydantic.md](01-fase-a-shared-core-pydantic.md)
- [02-fase-b-shared-db-sqlalchemy.md](02-fase-b-shared-db-sqlalchemy.md)
- [03-fase-c-shared-aws-ses-dynamodb.md](03-fase-c-shared-aws-ses-dynamodb.md)
- [04-fase-d-shared-observability-metricunit.md](04-fase-d-shared-observability-metricunit.md)
- [05-fase-e-migrar-services.md](05-fase-e-migrar-services.md)
- [06-fase-f-lint-deps-imports.md](06-fase-f-lint-deps-imports.md)
- [07-fase-g-claude-rule-skill-docs.md](07-fase-g-claude-rule-skill-docs.md)
- [08-verificacion-e2e.md](08-verificacion-e2e.md)
- [09-commits.md](09-commits.md)
- [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md)
