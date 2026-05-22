# 09 — Commits

[< 08 Descomposicion](08-descomposicion.md) | [Siguiente: 10 Worktrees >](10-paralelizacion-worktrees.md)

Branch: `feature/serverless-lambda-independence` desde `dev`. Un solo
PR `feature/serverless-lambda-independence -> dev`. Cada commit deja el
repo verde (lint + typecheck + tests del scope) y ejecuta su
verificacion incremental ANTES de commitear.

## Secuencia de commits

### C-1 — docs del plan

```
docs(specs): plan de independencia de los lambdas serverless

- agrega docs/specs/serverless-lambda-independence/ (11 archivos)
- descompone el refactor en 6 fases + verificacion E2E
- documenta las decisiones D-1..D-9 y los limites de AWS Lambda
```

Verificacion: `pnpm exec biome check docs/` (o markdownlint) sin errores.

### C-2 — auditoria de imports (T-1)

```
docs(serverless): audita imports de los core/ vs deps de shared

- mapea por lambda las libs externas directas vs las del cierre de shared
- cierra la lista de logica de dominio a mover a shared/db
- cierra la lista de deps duplicadas a eliminar de cada pyproject.toml
```

Verificacion: el documento clasifica las libs de los 4 Lambdas.

### C-3 — shared/db gana la logica de dominio (T-2)

```
feat(serverless): mueve la operativa de DB a shared/db

- crea shared/db/migrations.py (operativa Alembic: migrate/downgrade/...)
- crea shared/db/repository.py (queries ORM: list_tables, escritura stream)
- agrega tests unit de migrations y repository (coverage >= 80%)
```

Verificacion: `serverless tests --type=coverage --shared=db` verde.

### C-4 — shared/lambda_kit (T-3)

```
feat(serverless): crea shared/lambda_kit con utils y handlers genericos

- unifica base_controller, base_settings, import_controller (identicos x4)
- agrega dispatch.run_controller y los 3 handlers genericos por trigger
- unifica validation/event.py (investiga y resuelve la variante de stream)
- agrega tests unit del kit (coverage >= 80%)
```

Verificacion: `serverless tests --type=coverage --shared=lambda_kit` verde.

### C-5 — migra el lambda db (T-4)

```
refactor(serverless): el lambda db usa shared.db y shared.lambda_kit

- db/core/services/db_service.py delega en shared.db, sin alembic/sqlalchemy
- handler.py usa handler_direct generico
- elimina core/utils/{base_controller,base_settings,import_controller}.py
- el pyproject.toml de db ya no declara sqlalchemy/alembic/psycopg
```

Verificacion: `rg 'import (alembic|sqlalchemy)' .../db/core/` vacio;
`serverless run --stage=local --lambda=db --event=events/current.json` OK;
`serverless tests --type=coverage --lambda=db` verde.

### C-6 — migra el lambda stream_processor (T-5)

```
refactor(serverless): el lambda stream_processor usa shared.db

- la escritura ORM delega en shared.db.repository, sin sqlalchemy directo
- mantiene los transformers (logica de negocio propia)
- handler.py usa handler_stream generico
- elimina los core/utils/ duplicados; el pyproject.toml limpia las deps
```

Verificacion: `rg 'from sqlalchemy' .../stream_processor/core/` vacio;
`serverless tests --type=coverage --lambda=stream_processor` verde.

### C-7 — migra el lambda contact_form (T-6)

```
refactor(serverless): el lambda contact_form usa shared.lambda_kit

- handler.py usa handler_http generico
- elimina core/utils/{base_controller,base_settings,import_controller}.py
```

Verificacion: `serverless tests --type=coverage --lambda=contact_form` verde.

### C-8 — migra el lambda tracking_pixel (T-7)

```
refactor(serverless): el lambda tracking_pixel usa shared.lambda_kit

- handler.py usa handler_http generico
- elimina los core/utils/ duplicados
```

Verificacion: `serverless tests --type=coverage --lambda=tracking_pixel` verde.

### C-9 — venv aislado en devtools (T-8)

```
feat(devtools): gestion de venv aislado por lambda

- crea devtools/serverless/venv.py (uv sync + uv pip install del cierre)
- agrega tests unit del modulo
```

Verificacion: `serverless tests --type=unit --module=devtools` verde.

### C-10 — elimina el workspace uv (T-9)

```
refactor(serverless): elimina el workspace uv, cada lambda con su venv

- serverless/pyproject.toml sin [tool.uv.workspace] ni sources
- elimina serverless/uv.lock; cada lambda gana su uv.lock
- local_runtime y lambda_controller usan el venv aislado del lambda
```

Verificacion: `rg 'tool.uv.workspace' serverless/` vacio; `serverless
tests --type=unit --lambda=db` usa `db/.venv/bin/python`.

### C-11 — config de tooling descentralizada (T-10)

```
refactor(serverless): descentraliza ruff/mypy/pytest a cada pyproject

- cada lambda y subpaquete de shared lleva su config de tooling
- serverless/pyproject.toml reducido a metadata (o eliminado)
- lambda_controller resuelve --cov-config del paquete bajo test
```

Verificacion: `serverless lint` + `typecheck` + `tests` verdes.

### C-12 — validador de dedup (T-11)

```
feat(devtools): valida deps duplicadas entre lambda y shared

- crea serverless lint-deps: falla si un lambda declara una dep de shared
- el check se invoca dentro de package_lambda (build aborta temprano)
- agrega tests unit del validador
```

Verificacion: `serverless lint-deps` detecta/no-detecta segun el caso;
los 4 Lambdas pasan `lint-deps`.

### C-13 — control de peso del artefacto (T-12)

```
feat(devtools): warning y error de peso del artefacto del lambda

- crea artifact_size: mide build/ descomprimido y build.zip
- WARN al 80%, ERROR (aborta build) al pasar los limites de AWS Lambda
- tests y vendoring reportan el peso
```

Verificacion: build con tamano simulado WARN/ERROR; los 4 Lambdas pasan
sin warning.

### C-14 — docs y rules (T-13)

```
docs(rules): actualiza lambda-controller con el estado post-refactor

- documenta shared/lambda_kit, handlers genericos, venv aislado
- documenta la regla de dedup y el control de peso
- actualiza .claude/docs/serverless-backend/ y el arbol de conocimiento
```

Verificacion: los ejemplos de las rules reflejan la estructura nueva.

### C-15 — verificacion E2E (T-14, doc 11)

```
test(serverless): refactor de tests y verificacion E2E del backend

- ajusta tests que referenciaban codigo eliminado
- ejecuta la bateria completa de verificacion del doc 11
```

Verificacion: la bateria completa del doc 11 pasa.

## Resumen de secuencia

| # | Commit | Tarea | Verde tras |
|---|--------|-------|-----------|
| C-1 | plan | — | markdownlint |
| C-2 | auditoria | T-1 | doc completo |
| C-3 | shared/db logica | T-2 | tests shared=db |
| C-4 | shared/lambda_kit | T-3 | tests shared=lambda_kit |
| C-5 | lambda db | T-4 | tests + run db |
| C-6 | lambda stream | T-5 | tests stream |
| C-7 | lambda contact | T-6 | tests contact |
| C-8 | lambda tracking | T-7 | tests tracking |
| C-9 | venv devtools | T-8 | tests devtools |
| C-10 | sin workspace | T-9 | tests con venv aislado |
| C-11 | tooling descentralizado | T-10 | lint+typecheck+tests |
| C-12 | validador dedup | T-11 | lint-deps |
| C-13 | peso artefacto | T-12 | build size |
| C-14 | docs+rules | T-13 | markdownlint |
| C-15 | verificacion E2E | T-14 | bateria doc 11 |

Un solo PR `feature/serverless-lambda-independence -> dev`.

[< 08 Descomposicion](08-descomposicion.md) | [Siguiente: 10 Worktrees >](10-paralelizacion-worktrees.md)
