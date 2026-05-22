# 03 — Fase 2: Mover logica de dominio y utils duplicados a shared/

[< 02 Auditoria](02-fase-auditoria-imports.md) | [Siguiente: 04 Venv aislado >](04-fase-venv-aislado.md)

## Objetivo

Dos movimientos de codigo, ambos para que el `core/` de cada Lambda deje
de declarar libs que son de `shared/`:

- **2.A — Logica de dominio de DB a `shared/db`**: la operativa Alembic
  y la escritura ORM bajan a `shared/db`. El `core/` de `db` y
  `stream_processor` las consume via `from shared.db import ...`.
- **2.B — Utils duplicados a un `shared` nuevo**: `base_controller.py`,
  `base_settings.py`, `import_controller.py` son identicos en los 4
  Lambdas (verificado: solo difiere el formato del docstring). Se
  unifican en un subpaquete `shared/lambda_kit/`.

## 4. Diagrama de flujo

### Antes (Lambda `db`)

```text
core/handler.py
  -> core/controllers/db/<action>.py
       -> core/services/db_service.py
            from alembic import command   <-- core/ usa Alembic directo
            from sqlalchemy import ...     <-- core/ usa SQLAlchemy directo
```

### Despues (Lambda `db`)

```text
core/handler.py
  -> core/controllers/db/<action>.py
       -> core/services/db_service.py
            from shared.db.migrations import run_migrate, ...
            from shared.db.repository import list_tables
            (core/ NO importa alembic ni sqlalchemy)
shared/db/
  migrations.py   <-- operativa Alembic (run_migrate, downgrade, ...)
  repository.py   <-- queries ORM (list_tables, ...)
```

## 5. Diagrama ER

N/A — no cambia el schema. Los modelos SQLAlchemy de `shared/db/models/`
NO se tocan. Solo se mueve logica que los OPERA.

## Decision arquitectonica (resuelve el conflicto con lambda-controller)

El formato `lambda-controller` exige logica de negocio en
`core/services/`. La regla D-4 exige que el `core/` no use libs de
dominio de `shared/`. Se concilian asi:

- `shared/db` es el **dueno** de los modelos, la configuracion y la
  conexion de la DB, y de la API de dominio que las opera (Alembic,
  queries ORM).
- `core/services/` del Lambda **sigue existiendo** y sigue siendo la
  capa de negocio DEL LAMBDA: orquesta, pero invoca `shared.db.*`. NO
  importa `alembic` ni `sqlalchemy` — importa modelos, sesiones y
  funciones de `shared.db`.
- Los **transformers** de `stream_service.py` (`parse_contact_record`,
  `deserialize_image`, `_json_safe`, `detect_table`, `_to_int`, ...) NO
  usan SQLAlchemy: transforman dicts de DynamoDB. Son logica de negocio
  del `stream_processor` y SE QUEDAN en su `core/services/`.

## 2.A — Logica de dominio de DB a shared/db

### Que se mueve

| Origen | Destino | Funciones |
|--------|---------|-----------|
| `db/core/services/db_service.py` | `shared/db/migrations.py` (NUEVO) | `build_config`, `_capture`, `current_revision`, `run_migrate`, `run_downgrade`, `run_stamp`, `run_current`, `run_show_migrations` |
| `db/core/services/db_service.py` | `shared/db/repository.py` (NUEVO) | `run_tables` (query `pg_stat_user_tables`) |
| `stream_processor/core/services/stream_service.py` | `shared/db/repository.py` | `is_event_processed`, `mark_event_processed`, `insert_contact`, `insert_tracking`, y la escritura ORM de `process_record` |

`ServiceError` se mantiene donde lo consuma el controller (o se mueve a
`shared/core/exceptions` si ya hay un equivalente — decidir en la
auditoria fase 1).

### Que NO se mueve

- Los transformers de `stream_service.py` (no usan SQLAlchemy).
- `run_seed` (hoy es un stub que no toca la DB).
- El gancho de `_DB_MODULE` que apunta a `alembic.ini`: al estar la
  logica YA en `shared/db`, el path es relativo a `shared/db/` directo
  (mas simple — desaparece el `parents[1] / 'shared' / 'db'`).

### Como queda el core/

- `db/core/services/db_service.py`: orquestador delgado. Cada funcion
  llama a `shared.db.migrations.*` / `shared.db.repository.*`. Mantiene
  el contrato `{is_valid, data, code}` hacia el controller.
- `stream_processor/core/services/stream_service.py`: mantiene los
  transformers; `process_record` orquesta llamando a
  `shared.db.repository.*` para la escritura.

## 2.B — Utils duplicados a shared/lambda_kit/

### Que se unifica

| Archivo (x4 Lambdas, identico) | Destino |
|--------------------------------|---------|
| `core/utils/base_controller.py` | `shared/lambda_kit/base_controller.py` |
| `core/utils/base_settings.py` | `shared/lambda_kit/base_settings.py` |
| `core/utils/import_controller.py` | `shared/lambda_kit/import_controller.py` |

Nombre del subpaquete: `lambda_kit` (kit comun del estandar
lambda-controller). Confirmar el nombre en la auditoria si hay uno
mejor; el plan usa `lambda_kit`.

### handler.py — handler generico por TIPO de trigger (Decision D-8)

Los `handler.py` DIFIEREN porque cada Lambda traduce un evento distinto.
La solucion: `shared/lambda_kit/` provee TRES handlers genericos, uno
por tipo de trigger del backend:

| Handler generico | Trigger | Lo usan |
|------------------|---------|---------|
| `handler_http` | API Gateway REST proxy | `contact_form`, `tracking_pixel` |
| `handler_direct` | invocacion directa `{command, args}` | `db` |
| `handler_stream` | DynamoDB Streams `{Records: [...]}` | `stream_processor` |

Cada handler generico encapsula: parsear SU tipo de evento, sintetizar
el contrato `{operation, action, data}`, correr el ciclo
`validate_event -> controller -> run()`, y normalizar la salida (HTTP
para `handler_http`, dict para los otros).

El `core/handler.py` de cada Lambda queda MINIMO: declara que handler
generico usa y le pasa su config (la `operation`/`action` o el mapa de
`command`, las metricas, el `__version__`). Casi cero codigo de handler
por Lambda.

El tipo de trigger ya esta declarado en `manifest.yaml`
(`trigger.type: http|direct|on-table-changes`) — el plan reutiliza ese
dato para validar que el Lambda usa el handler generico correcto.

### validation/event.py — unificar (Decision D-9)

Es identico en 3 de 4 Lambdas; `stream_processor` tiene una variante.
La fase 1 (auditoria) DEBE investigar por que difiere:

- Si la diferencia es **drift accidental**: unificar al generico de
  `shared/lambda_kit/validation/event.py`, los 4 Lambdas lo usan.
- Si la diferencia es **necesaria** (el evento de Streams es
  estructuralmente distinto): el generico de `lambda_kit` se hace
  parametrizable para soportar ambos casos — NO se deja una copia
  por-Lambda. El objetivo es cero duplicacion.

### Imports tras la unificacion

`from utils.base_controller import BaseController`
-> `from shared.lambda_kit.base_controller import BaseController`.

El `core/utils/` de cada Lambda queda solo con lo especifico del Lambda
(si queda algo) o se elimina si todo era comun.

## 6. Tests requeridos

### 6.B Unit tests (TDD estricto — Red primero)

- `shared/db/tests/unit/test_migrations_*.py` — un archivo por escenario
  para `run_migrate`, `run_downgrade`, `run_stamp`, `run_current`,
  `run_show_migrations`, `current_revision`. Mockear Alembic `command.*`;
  NO mockear `build_config`. [AC-11]
- `shared/db/tests/unit/test_repository_*.py` — `list_tables`,
  `is_event_processed`, `mark_event_processed`, `insert_contact`,
  `insert_tracking`. Mockear la Session ORM. [AC-11]
- `shared/lambda_kit/tests/unit/test_*.py` — `BaseController`,
  `base_settings`, `import_controller`, `run_controller`. [AC-12]
- Los tests existentes de `db_service` / `stream_service` que cubrian la
  logica movida se ADAPTAN: ahora prueban que el `core/services/`
  orquesta (llama al `shared.db.*` correcto) — mockeando `shared.db`.

### 6.C Typecheck

- `mypy` sobre `shared/db/` y `shared/lambda_kit/` tras crearlos.

### 6.D E2E

- `serverless run --stage=local --lambda=db --event=events/current.json`
  modo directo: el handler responde igual que antes. [AC-13]
- Igual para `stream_processor` con un event de Stream.

## 7. Archivos afectados

### Crear

- `serverless/lambda/shared/db/migrations.py` — operativa Alembic.
  - Verificar: `serverless tests --type=unit --shared=db` verde.
- `serverless/lambda/shared/db/repository.py` — queries ORM.
  - Verificar: idem.
- `serverless/lambda/shared/lambda_kit/__init__.py`
- `serverless/lambda/shared/lambda_kit/pyproject.toml` — declara
  `pydantic` (lo usa `base_controller`), `internal-deps` segun lo que
  importe (`observability` si usa el logger).
  - Verificar: `tomllib` parsea el archivo sin error.
- `serverless/lambda/shared/lambda_kit/base_controller.py`
- `serverless/lambda/shared/lambda_kit/base_settings.py`
- `serverless/lambda/shared/lambda_kit/import_controller.py`
- `serverless/lambda/shared/lambda_kit/dispatch.py` — `run_controller`.
- `serverless/lambda/shared/lambda_kit/tests/` — suite unit.
- `serverless/lambda/shared/db/tests/unit/test_migrations_*.py`
- `serverless/lambda/shared/db/tests/unit/test_repository_*.py`

### Modificar

- `serverless/lambda/shared/db/pyproject.toml` — sin cambios de deps
  (sqlalchemy/alembic/psycopg ya estan); si `migrations.py` necesita
  algo mas, agregarlo aqui.
- `serverless/lambda/services/db/core/services/db_service.py` — delega
  en `shared.db.*`, sin `import alembic` ni `sqlalchemy`.
  - Verificar: `rg 'import (alembic|sqlalchemy)' .../db/core/` vacio.
- `serverless/lambda/services/stream_processor/core/services/stream_service.py`
  — la escritura ORM delega en `shared.db.repository`; mantiene
  transformers. Sin `from sqlalchemy import select` ni `Session`.
  - Verificar: `rg 'from sqlalchemy' .../stream_processor/core/` vacio.
- Los 4 `core/handler.py` — imports de `utils.*` -> `shared.lambda_kit.*`;
  router delega en `run_controller`.
- Los `core/controllers/**/*.py` de los 4 Lambdas — imports de
  `utils.base_controller` -> `shared.lambda_kit.base_controller`.
- Los `core/settings/config.py` — si usan `base_settings`, ajustar el
  import.

### Eliminar

- `serverless/lambda/services/*/core/utils/base_controller.py` (x4)
- `serverless/lambda/services/*/core/utils/base_settings.py` (x4)
- `serverless/lambda/services/*/core/utils/import_controller.py` (x4)
- `serverless/lambda/services/db/core/services/db_service.py` logica
  movida (el archivo se mantiene como orquestador, mas chico).

## Definition of Done de la fase

- [ ] `shared/db/migrations.py` + `repository.py` creados con tests
      unit verdes, coverage per-file >= 80%.
- [ ] `shared/lambda_kit/` creado con los 3 utils + `dispatch.py` +
      tests verdes.
- [ ] El `core/` de `db` NO importa `alembic` ni `sqlalchemy`.
- [ ] El `core/` de `stream_processor` NO importa `sqlalchemy`.
- [ ] Los 4 Lambdas NO tienen `core/utils/base_controller.py` etc.
- [ ] `serverless run --stage=local` de `db` y `stream_processor`
      responde igual que antes (AC-13).
- [ ] `serverless tests --type=coverage` (todo) verde.

[< 02 Auditoria](02-fase-auditoria-imports.md) | [Siguiente: 04 Venv aislado >](04-fase-venv-aislado.md)
