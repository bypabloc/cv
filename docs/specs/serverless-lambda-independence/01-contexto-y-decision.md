# 01 — Contexto, solucion y criterios de aceptacion

[< README](README.md) | [Siguiente: 02 Auditoria >](02-fase-auditoria-imports.md)

## 1. Contexto / Problema

El backend serverless del portfolio tiene 4 Lambdas Python
(`contact_form`, `tracking_pixel`, `stream_processor`, `db`) que
comparten una libreria comun en `serverless/lambda/shared/` (8
subpaquetes con `pyproject.toml` propio). Hoy:

1. **`serverless/pyproject.toml` es un workspace uv** que crea UN solo
   `.venv` con la union de las deps de los 4 Lambdas. `run --stage=local`
   (modo directo), `tests` de cada Lambda y `tests` de `shared/` usan ese
   `.venv` compartido (`local_runtime.py:59`,
   `lambda_controller.py:52`, `_resolve_pytest_python`).
2. **Las deps estan duplicadas**: `lambda/services/db/pyproject.toml`
   declara `sqlalchemy`, `alembic`, `psycopg` — exactamente lo mismo que
   `lambda/shared/db/pyproject.toml`. El `core/` del Lambda `db` SI las
   importa directo (`core/services/db_service.py: from alembic`), igual
   que `stream_processor` importa `from sqlalchemy` en su
   `core/services/stream_service.py`.

### Hallazgos de exploracion

- `packaging.py:235` ya hace `all_deps = lambda_deps | shared_deps`: el
  vendoring SI une ambas. La duplicacion en el `pyproject.toml` del
  Lambda no rompe el build, pero es ruido y deja una bomba de tiempo.
- El problema de fondo: el `core/` de `db` y `stream_processor` ejecuta
  logica de dominio (Alembic, queries SQLAlchemy) que conceptualmente
  pertenece a `shared/db`. Mientras esa logica viva en el `core/`, el
  Lambda DEBE declarar esas libs y la duplicacion es inevitable.
- El `.venv` compartido hace que `run --stage=local` y `tests` NO sean
  fieles a la realidad de produccion: en AWS cada Lambda corre solo con
  SUS deps, no con la union de las de los 4.

### Por que el cambio

Pablo lo pide explicito: cada Lambda debe ser **independiente** —
tests, run-local y build lo mas parecido a la realidad de AWS. Y la
duplicacion de deps debe desaparecer: las libs de un `shared/<sub>` son
responsabilidad EXCLUSIVA de ese subpaquete; el `core/` del Lambda usa
los ARCHIVOS de `shared`, no sus librerias.

## 2. Solucion Propuesta

Refactorizacion en 6 fases (+ verificacion E2E):

1. **Auditoria de imports**: mapear, por cada `core/`, que libs importa
   directo y cuales le llegan via `shared/`. Output: la lista exacta de
   logica a mover y de deps a eliminar de cada `pyproject.toml`.
2. **Mover logica de dominio a `shared/db`**: la operativa Alembic
   (`db_service.py`) y la query SQLAlchemy (`stream_service.py`) se
   mueven a funciones de `shared/db`. Los `core/` quedan como
   orquestadores delgados que solo importan `from shared.db import ...`.
3. **Venv aislado + eliminar workspace**: cada Lambda gana su `.venv`
   propio gestionado con `uv sync`. Se elimina el workspace uv de
   `serverless/pyproject.toml`. devtools resuelve el cierre de `shared/`
   (ya lo hace `shared_resolver`) e instala esas deps extra en el `.venv`
   del Lambda con `uv sync` + `uv pip install`.
4. **Tooling descentralizado**: cada Lambda y cada subpaquete de
   `shared/` lleva su `[tool.ruff]`, `[tool.pytest]`, `[tool.coverage]`,
   `[tool.mypy]` en su `pyproject.toml`. `serverless/pyproject.toml`
   queda como archivo minimo (o se elimina si nada lo necesita).
5. **Validador de dedup**: un check en devtools que escanea el `core/`
   de cada Lambda y FALLA si su `pyproject.toml` declara una lib que ya
   le llega por el cierre transitivo de `shared/`.
6. **Peso del artefacto**: el packaging mide el zip comprimido y el
   build descomprimido; avisa al 80% del limite de AWS y aborta el build
   al pasarlo. El vendoring/tests tambien reportan el peso.

### Decisiones clave

- **Decision 1: venv aislado on-demand via `uv sync`** — cada Lambda
  tiene `<lambda>/.venv`. devtools corre `uv sync` (deps de runtime +
  grupo dev del Lambda) y luego instala las deps externas del cierre de
  `shared/` con `uv pip install`. El `.venv` refleja exactamente lo que
  el Lambda necesita, sin contaminacion de los otros 3.
- **Decision 2: eliminar el workspace uv** — sin `.venv` compartido, el
  workspace pierde sentido. Cada Lambda y cada subpaquete de `shared/`
  tiene su `uv.lock` independiente. `serverless/uv.lock` se elimina.
- **Decision 3: regla estricta de dedup** — si una lib llega al Lambda
  por el cierre de `shared/`, el `pyproject.toml` del Lambda NO la
  declara, sea cual sea (incluye `pydantic`, `boto3`, `powertools` si
  vienen de `shared.observability`/`shared.aws`). El `pyproject.toml`
  del Lambda declara SOLO lo que su `core/` importa y `shared/` NO
  aporta. Riesgo asumido: si un Lambda deja de usar todo `shared/`, su
  `core/` se queda sin esas libs en el zip — el validador de la fase 5
  y los tests de la fase 7 lo detectan.
- **Decision 4: logica de dominio en `shared/db`** — los `core/` de
  `db` y `stream_processor` no deben ejecutar Alembic ni SQLAlchemy
  directo. Esa logica se mueve a `shared/db` (funciones publicas). Los
  `core/` orquestan.
- **Decision 5: tooling por paquete** — cada `pyproject.toml` (Lambda y
  subpaquete de `shared/`) es autonomo: trae su config de ruff, mypy,
  pytest, coverage. Igual que `devtools/ruff.toml`.
- **Decision 6: peso reportado en ambas cifras** — el warning informa
  zip comprimido (vs 50 MB) y descomprimido (vs 250 MB). El build aborta
  si cualquiera pasa su hard limit.
- **Decision 7: `uv sync` siempre** — cada corrida de `tests`
  re-sincroniza el `.venv` del Lambda. `uv sync` es rapido si el lock no
  cambio (solo verifica). Garantiza cero drift pyproject vs venv.

### Constraints considerados

- El runtime de AWS Lambda sigue siendo `python3.13` (AWS no ofrece
  3.14). devtools corre en 3.14. Sin cambios aqui.
- El comportamiento observable del backend NO debe cambiar: mover
  logica a `shared/db` es un refactor interno, los 4 Lambdas siguen
  respondiendo igual.
- El packaging para deploy (`uv pip install --target` con
  `--python-platform aarch64`) NO cambia: sigue armando el artefacto
  arm64. El `.venv` aislado es para run-local (modo directo) y tests en
  el host — son x86, no se mezclan con el artefacto de deploy.

## 3. Criterios de Aceptacion (AC)

Formato BDD (Given/When/Then). Fuente de verdad — los tests y las
tareas los referencian.

- **AC-1**: Given el backend serverless, When se inspecciona
  `serverless/pyproject.toml`, Then NO contiene `[tool.uv.workspace]` ni
  `[tool.uv.sources]` y `serverless/uv.lock` no existe.

- **AC-2**: Given un Lambda cualquiera, When se corre
  `serverless tests --type=unit --lambda=<x>`, Then los tests se
  ejecutan con el interprete `<lambda>/.venv/bin/python` y NO con
  `serverless/.venv/bin/python`.

- **AC-3**: Given el Lambda `db`, When se inspecciona su
  `pyproject.toml`, Then NO declara `sqlalchemy`, `alembic` ni `psycopg`
  (le llegan via el cierre de `shared/db`).

- **AC-4**: Given el Lambda `stream_processor`, When se inspecciona su
  `pyproject.toml`, Then NO declara `sqlalchemy` ni `psycopg`.

- **AC-5**: Given el `core/` del Lambda `db`, When se escanean sus
  imports, Then NO importa `alembic` ni `sqlalchemy` directo — solo
  `from shared.db import ...`.

- **AC-6**: Given el `core/` del Lambda `stream_processor`, When se
  escanean sus imports, Then NO importa `sqlalchemy` directo — solo
  `from shared.db import ...`.

- **AC-7**: Given un Lambda con una dep en su `pyproject.toml` que ya
  llega por el cierre de `shared/`, When se corre el validador de dedup,
  Then el validador FALLA (exit code != 0) e indica la lib y el
  subpaquete de `shared/` que ya la aporta.

- **AC-8**: Given un Lambda cuyo `pyproject.toml` NO duplica deps de
  `shared/`, When se corre el validador de dedup, Then el validador pasa
  (exit code 0).

- **AC-9**: Given un `deploy` o `build` de un Lambda, When el artefacto
  comprimido supera 50 MB o el descomprimido supera 250 MB, Then el
  comando FALLA con error e indica ambas cifras y el limite excedido.

- **AC-10**: Given un `deploy`/`build`/`tests` de un Lambda, When el
  artefacto se acerca al limite (zip > 40 MB o descomprimido > 200 MB),
  Then se imprime un `[WARN]` con ambas cifras y los limites de AWS.

- **AC-11**: Given la logica Alembic movida a `shared/db`, When se
  corren los tests de `shared/db`, Then la operativa de migracion
  (`upgrade`, `downgrade`, `current`, `stamp`, etc.) esta cubierta por
  tests unit con coverage per-file >= 80%.

- **AC-12**: Given el backend completo tras el refactor, When se corre
  `serverless tests --type=coverage` (los 4 Lambdas + shared), Then todo
  pasa verde con coverage per-file >= 80%.

- **AC-13**: Given el Lambda `db` tras el refactor, When se corre
  `serverless run --stage=local --lambda=db --event=events/current.json`
  en modo directo, Then el handler responde igual que antes del refactor
  (comportamiento observable sin cambios).

[< README](README.md) | [Siguiente: 02 Auditoria >](02-fase-auditoria-imports.md)
