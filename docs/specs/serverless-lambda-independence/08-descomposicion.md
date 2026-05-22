# 08 — Descomposicion para paralelizacion

[< 07 Peso artefacto](07-fase-peso-artefacto.md) | [Siguiente: 09 Commits >](09-commits.md)

## Tamano del plan

**Large**: toca devtools (3 modulos nuevos + 5 modificados), los 4
Lambdas, varios subpaquetes de `shared/`, docs y rules. ~30+ archivos.

## Tareas atomicas

Cada tarea pasa los 3 checks (File Exclusivity, Interface Stability,
Bounded Scope) y trae 6 campos.

### T-1 — Auditoria de imports

- **Archivos**: `docs/progress/explore_serverless_deps_audit.md` (crear)
- **AC**: base de AC-3..AC-6
- **Depende de**: nada
- **Paralelizable con**: nada (es la base — todo lo demas la usa)
- **Verify**: el documento clasifica las libs de los 4 Lambdas
- **Done**: lista cerrada de logica a mover + deps a borrar

### T-2 — `shared/db/migrations.py` + `repository.py` (TDD)

- **Archivos**: `serverless/lambda/shared/db/migrations.py`,
  `serverless/lambda/shared/db/repository.py`,
  `serverless/lambda/shared/db/tests/unit/test_migrations_*.py`,
  `serverless/lambda/shared/db/tests/unit/test_repository_*.py`,
  `serverless/lambda/shared/db/pyproject.toml`
- **AC**: AC-11
- **Depende de**: T-1
- **Paralelizable con**: T-3
- **Verify**: `serverless tests --type=coverage --shared=db` verde
- **Done**: logica de dominio en `shared/db`, tests verdes >= 80%

### T-3 — `shared/lambda_kit/` (utils + handlers genericos, TDD)

- **Archivos**: todo `serverless/lambda/shared/lambda_kit/**`
  (`base_controller.py`, `base_settings.py`, `import_controller.py`,
  `dispatch.py`, `handler_http.py`, `handler_direct.py`,
  `handler_stream.py`, `validation/event.py`, `pyproject.toml`,
  `__init__.py`, `tests/**`)
- **AC**: AC-12
- **Depende de**: T-1
- **Paralelizable con**: T-2
- **Verify**: `serverless tests --type=coverage --shared=lambda_kit` verde
- **Done**: subpaquete creado, tests verdes >= 80%

### T-4 — Migrar Lambda `db` al nuevo shared

- **Archivos**: `serverless/lambda/services/db/core/**` (handler,
  services, controllers, utils, settings), `db/.gitignore`
- **AC**: AC-3, AC-5, AC-13
- **Depende de**: T-2, T-3
- **Paralelizable con**: T-5, T-6, T-7 (archivos disjuntos por Lambda)
- **Verify**: `rg 'import (alembic|sqlalchemy)' db/core/` vacio;
  `serverless run --stage=local --lambda=db` OK
- **Done**: `db` usa `shared.db` + `shared.lambda_kit`, sin libs propias

### T-5 — Migrar Lambda `stream_processor`

- **Archivos**: `serverless/lambda/services/stream_processor/core/**`,
  `.gitignore`
- **AC**: AC-4, AC-6, AC-13
- **Depende de**: T-2, T-3
- **Paralelizable con**: T-4, T-6, T-7
- **Verify**: `rg 'from sqlalchemy' stream_processor/core/` vacio
- **Done**: `stream_processor` usa `shared.db` + `shared.lambda_kit`

### T-6 — Migrar Lambda `contact_form`

- **Archivos**: `serverless/lambda/services/contact_form/core/**`,
  `.gitignore`
- **AC**: AC-12
- **Depende de**: T-3
- **Paralelizable con**: T-4, T-5, T-7
- **Verify**: `serverless tests --type=unit --lambda=contact_form` verde
- **Done**: usa `shared.lambda_kit`, sin `core/utils/` duplicado

### T-7 — Migrar Lambda `tracking_pixel`

- **Archivos**: `serverless/lambda/services/tracking_pixel/core/**`,
  `.gitignore`
- **AC**: AC-12
- **Depende de**: T-3
- **Paralelizable con**: T-4, T-5, T-6
- **Verify**: `serverless tests --type=unit --lambda=tracking_pixel` verde
- **Done**: usa `shared.lambda_kit`, sin `core/utils/` duplicado

### T-8 — `devtools/serverless/venv.py` (venv aislado, TDD)

- **Archivos**: `devtools/serverless/venv.py`,
  `devtools/tests/serverless/test_venv_*.py`
- **AC**: AC-2
- **Depende de**: nada (interfaz nueva)
- **Paralelizable con**: T-2..T-7
- **Verify**: tests unit de `venv` verdes
- **Done**: modulo creado con tests >= 80%

### T-9 — Eliminar workspace uv + integrar venv aislado

- **Archivos**: `serverless/pyproject.toml`, `serverless/uv.lock`
  (borrar), `devtools/serverless/local_runtime.py`,
  `devtools/serverless/lambda_controller.py`
- **AC**: AC-1, AC-2
- **Depende de**: T-8, y T-4..T-7 (los Lambdas deben estar migrados
  antes de cambiar como se resuelve su venv)
- **Paralelizable con**: nada (toca config central + 2 modulos
  compartidos de devtools)
- **Verify**: `rg 'tool.uv.workspace' serverless/`; `serverless tests`
  usa el `.venv` del Lambda
- **Done**: workspace eliminado, devtools usa venv aislado

### T-10 — Config de tooling descentralizada

- **Archivos**: los 12 `pyproject.toml` (4 Lambdas + 8 `shared/`),
  `serverless/pyproject.toml`, `devtools/serverless/quality.py`
- **AC**: AC-12
- **Depende de**: T-9
- **Paralelizable con**: nada (toca todos los pyproject + quality.py)
- **Verify**: `serverless lint` + `typecheck` + `tests` verdes
- **Done**: tooling por paquete, raiz minimo/eliminado

### T-11 — Validador de dedup

- **Archivos**: `devtools/serverless/dep_validator.py`,
  `devtools/tests/serverless/test_lint_deps_*.py`,
  `devtools/serverless/flags.py`, `devtools/serverless/main.py`,
  `devtools/serverless/help.py`, `devtools/serverless/packaging.py`
- **AC**: AC-7, AC-8
- **Depende de**: T-9 (los pyproject de los Lambdas ya sin deps de
  shared)
- **Paralelizable con**: T-12 (artifact_size toca packaging.py tambien
  -> ver colision en doc 10)
- **Verify**: `serverless lint-deps` detecta/no-detecta segun el caso
- **Done**: comando + check en build, tests >= 80%

### T-12 — Control de peso del artefacto

- **Archivos**: `devtools/serverless/artifact_size.py`,
  `devtools/tests/serverless/test_artifact_size_*.py`,
  `devtools/serverless/packaging.py`, `devtools/serverless/vendoring.py`,
  `devtools/serverless/lambda_controller.py`
- **AC**: AC-9, AC-10
- **Depende de**: T-9
- **Paralelizable con**: T-11 con cuidado — ambas tocan `packaging.py`.
  Ver doc 10: se serializan o una hace el merge.
- **Verify**: build con tamano simulado WARN/ERROR
- **Done**: warning + error de peso, tests >= 80%

### T-13 — Docs + rules

- **Archivos**: `.claude/rules/lambda-controller.md`,
  `.claude/docs/serverless-backend/**`, `CLAUDE.md` (arbol de
  conocimiento si cambia), `serverless/lambda/shared/README.md` si
  existe
- **AC**: ninguno directo (documentacion)
- **Depende de**: T-1..T-12 (documenta el estado final)
- **Paralelizable con**: nada (fase de cierre, antes de T-14)
- **Verify**: los ejemplos de las rules reflejan la estructura nueva
- **Done**: rules actualizadas (handler generico, lambda_kit, venv
  aislado, sin workspace, validador dedup, peso)

### T-14 — Verificacion E2E (doc 11)

- **Archivos**: tests que referencien codigo eliminado (ajuste final)
- **Depende de**: TODO
- **Paralelizable con**: nada — es la ultima fase

## Limite de concurrencia

Max 5-7 agentes. Pico real: T-4..T-7 (4 Lambdas) + T-8 = 5 tareas
concurrentes.

## Anti-patrones evitados

- T-4..T-7 tocan archivos disjuntos (un `core/` por Lambda) -> sin race.
- T-9, T-10, T-11+T-12 tocan `devtools/serverless/` compartido ->
  secuenciales o con merge controlado (doc 10).
- T-2 y T-3 son subpaquetes de `shared/` distintos -> paralelos.

[< 07 Peso artefacto](07-fase-peso-artefacto.md) | [Siguiente: 09 Commits >](09-commits.md)
