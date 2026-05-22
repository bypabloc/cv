# Commit 2 — CLI: unificar `tests` y `run`

> [README](README.md) | Siguiente: [02 — resources](02-commit-3-resources.md)

## Objetivo

Reemplazar 4 comandos de test por uno (`tests`) y 2 comandos de
ejecucion por uno (`run`).

## Cambios de comandos

| Antes | Despues |
|-------|---------|
| `test-unit --lambda=X` | `tests --type=unit --lambda=X` |
| `test-integration --lambda=X` | `tests --type=integration --lambda=X` |
| `test` (shared) | `tests --type=unit --shared` |
| `test-coverage` (shared) | `tests --type=coverage --shared` |
| `run-local --lambda=X` | `run --stage=local --lambda=X` |
| `invoke-remote --stage=dev --lambda=X` | `run --stage=dev --lambda=X` |

## Diseno de `tests`

Un solo comando con:

- `--type=unit|integration|coverage` (obligatorio). `coverage` corre
  pytest con `--cov` + `--cov-fail-under` (threshold de
  `--coverage-threshold`, default 80).
- Target, en orden de precedencia:
  - `--lambda=<nombre>`: tests del Lambda
    (`lambda/services/<nombre>/tests/<type>`).
  - `--shared`: tests de toda la libreria comun
    (`lambda/shared/tests/`).
  - `--shared=<subpaquete>`: solo ese subpaquete
    (`lambda/shared/tests/` filtrado por `aws`, `cache`, etc. — ver
    nota de implementacion).
  - sin target: corre TODO (los 4 lambdas + shared).
- `integration` para `--shared` puede no aplicar (la libreria comun no
  tiene integration tests hoy): si el directorio no existe, reportar
  skip, no error.

### Nota: `--shared=<subpaquete>`

Hoy `lambda/shared/tests/` tiene solo `unit/`. Si los tests de shared
estan organizados por subpaquete (`tests/unit/aws/`, `tests/unit/cache/`)
el filtro es trivial (pasar el subdir a pytest). Si estan planos,
`--shared=<subpaquete>` filtra por `-k <subpaquete>` o por path de
archivo. Verificar la estructura real de `lambda/shared/tests/unit/`
antes de implementar y elegir el mecanismo.

## Diseno de `run`

Un solo comando, el `--stage` decide el mecanismo:

- `--stage=local` -> `sam local invoke` (codigo actual, contenedor
  Docker local). Es el `cmd_run_local` actual.
- `--stage=dev|stage|prod` -> `aws lambda invoke` contra la funcion
  `portfolio-<name>-<stage>` ya deployada. Es el `cmd_invoke_remote`
  actual.
- `--event=<path>` y `--debug` siguen igual.

`run` exige `--lambda` o `--path` (modo lambda-controller).

## Archivos afectados

### Modificar
- `devtools/serverless/flags.py`
  - `VALID_COMMANDS`: quitar `test-unit`, `test-integration`, `test`,
    `test-coverage`, `run-local`, `invoke-remote`; agregar `tests`,
    `run`.
  - `ALLOWED_FLAGS`: agregar `type`. (`shared` se modela como flag con
    valor opcional: `--shared` o `--shared=aws`.)
  - `PATH_REQUIRED_COMMANDS`: `run` lo requiere; `tests` NO (puede
    correr todo o `--shared`).
  - Validacion nueva: `tests` exige `--type` valido; `run` con
    `--stage=local` vs deployado.
  - `_COMMAND_SUMMARIES`, `_COMMAND_FLAGS`, `describe()`: actualizar.
  - Verificar: `devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/`
- `devtools/serverless/main.py`
  - `COMMAND_REGISTRY`: quitar las 6 entradas viejas, agregar `tests` y
    `run`.
  - Verificar: `python devtools/run.py serverless help`
- `devtools/serverless/lambda_controller.py`
  - Fusionar `cmd_run_local` + `cmd_invoke_remote` en `cmd_run` que
    despacha por `--stage`.
  - Fusionar `cmd_test_unit_lambda` + `cmd_test_integration_lambda` +
    integrar la logica de `testing.py` (`cmd_test`/`cmd_test_coverage`)
    en `cmd_tests` que despacha por `--type` y target.
- `devtools/serverless/testing.py`
  - Absorbido por `cmd_tests`. El modulo puede quedar como helpers de
    pytest (`_pytest_base_args`) o eliminarse si `cmd_tests` queda en
    `lambda_controller.py`. Decidir en implementacion.
- `devtools/serverless/help.py`
  - `_GROUPS`: reflejar `tests` y `run`, quitar los 6 viejos.

### Tests
- `devtools/tests/unit/src/serverless/test_flags*.py` — actualizar a la
  nueva grilla de comandos.

## Criterios de aceptacion

- AC-1: `serverless tests --type=unit --lambda=contact_form` corre
  `pytest tests/unit` del Lambda.
- AC-2: `serverless tests --type=coverage --shared` corre pytest con
  `--cov` sobre `lambda/shared/tests/`.
- AC-3: `serverless tests --type=unit --shared=aws` corre solo el
  subpaquete `aws`.
- AC-4: `serverless tests --type=unit` sin target corre todo.
- AC-5: `serverless run --stage=local --lambda=db --event=events/migrate.json`
  ejecuta `sam local invoke`.
- AC-6: `serverless run --stage=dev --lambda=db --event=events/migrate.json`
  ejecuta `aws lambda invoke` contra `portfolio-db-dev`.
- AC-9: `serverless help` ya no lista `test-*`/`run-local`/`invoke-remote`.

## Verificacion (sin AWS)

```bash
devtools/.venv/bin/python -m compileall -q devtools/serverless
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/ -q
python devtools/run.py serverless help
python devtools/run.py serverless tests --type=unit --lambda=db   # smoke
```

## Definition of Done

- [ ] Los 6 comandos viejos ya no existen; `tests` y `run` funcionan.
- [ ] Tests de `devtools/tests/unit/src/serverless/` verdes.
- [ ] `serverless help` refleja la grilla nueva.
- [ ] `compileall` sin errores.

---

[README](README.md) | Siguiente: [02 — resources](02-commit-3-resources.md)
