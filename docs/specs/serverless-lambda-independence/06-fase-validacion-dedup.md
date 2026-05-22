# 06 — Fase 5: Validador automatico de deps duplicadas

[< 05 Config tooling](05-fase-config-tooling.md) | [Siguiente: 07 Peso artefacto >](07-fase-peso-artefacto.md)

## Objetivo

Un check en devtools que escanea cada Lambda y FALLA si su
`pyproject.toml` declara una dependencia que ya le llega por el cierre
transitivo de `shared/`. Es el enforcement de la regla D-3: sin esto, la
duplicacion vuelve a aparecer sin que nada lo detecte.

## 4. Diagrama de flujo

```text
serverless lint-deps --lambda=<x>   (o integrado en deploy/build)
  -> shared_resolver.resolve_lambda_shared(lambda)
       -> (closure, shared_external_deps)
  -> leer [project.dependencies] del pyproject del Lambda
  -> normalizar nombres (canonical PEP 503: minusculas, guion)
  -> interseccion = lambda_deps & shared_external_deps
  -> {interseccion vacia}? --SI--> OK (exit 0)
                          --NO--> ERROR (exit 1): lista las libs
                                  duplicadas + el subpaquete shared
                                  que ya las aporta
```

## 5. Diagrama ER

N/A.

## Regla de comparacion

- La dependencia se compara por **nombre canonico** (PEP 503:
  minusculas, `_`/`.` -> `-`), NO por el spec completo. `psycopg[binary]`
  y `psycopg` son la misma lib. `aws-lambda-powertools[all]` y
  `aws_lambda_powertools` tambien.
- La regla D-3 es **estricta**: si la lib esta en el cierre de `shared/`,
  el Lambda NO la declara — sin importar cual sea (incluye `pydantic`,
  `boto3`, `aws-lambda-powertools`).
- El validador reporta, por cada lib duplicada: el nombre, el spec del
  Lambda, y QUE subpaquete(s) de `shared/` la aportan.

## Riesgo de la regla estricta (D-3) — documentado

Si un Lambda declara `pydantic` en su `core/` pero `pydantic` ya viene
de `shared.observability`, bajo D-3 el Lambda NO lo declara. Consecuencia:
si ese Lambda algun dia deja de importar CUALQUIER `shared/`, su `core/`
se queda sin `pydantic` en el zip.

Mitigacion:

- El validador de esta fase corre en cada `deploy`/`build`: si el cierre
  de `shared/` cambia y una lib deja de estar cubierta, el packaging
  fallaria al faltar la dep. La fase 7 (peso) y los tests E2E lo
  detectan antes de prod.
- En la practica, los 4 Lambdas del backend SIEMPRE usan
  `shared.observability` (todos importan el logger) — `pydantic` y las
  libs base estan garantizadas mientras eso se cumpla. El validador
  podria, opcionalmente, ADVERTIR (no fallar) si una lib critica
  depende de un solo subpaquete de `shared/`.

## Integracion

- Comando nuevo: `serverless lint-deps` (`--lambda=<x>` o sin target
  para los 4). Agregar a `VALID_COMMANDS` en `flags.py`.
- Ademas, el check se invoca DENTRO de `package_lambda` (fase 7 lo
  encadena): el `deploy`/`build` falla temprano si hay duplicacion, sin
  llegar a armar el zip.

## 6. Tests requeridos

### 6.A TDD flows

- `WHEN lint-deps con un lambda que declara psycopg Y usa shared.db
  THEN falla e indica psycopg + shared/db [AC-7]`
- `WHEN lint-deps con un lambda sin deps duplicadas THEN pasa (exit 0) [AC-8]`
- `WHEN un lambda declara psycopg[binary] y shared aporta psycopg THEN
  se detecta como la misma lib (normalizacion canonica) [AC-7]`

### 6.B Unit tests (devtools, pytest)

- `devtools/tests/serverless/test_lint_deps_*.py` — un archivo por
  escenario. Fixtures con `pyproject.toml` sinteticos + un `shared/`
  fake (override `shared_dir`, como ya hace `shared_resolver`).
- Asserts EXACTOS: `assert result.duplicated == ['psycopg']`,
  `assert exit_code == 1`.

### 6.C Typecheck

- `mypy` del nuevo modulo (corre en `devtools/.venv`).

## 7. Archivos afectados

### Crear

- `devtools/serverless/dep_validator.py` — logica del check: resuelve el
  cierre, normaliza nombres, calcula la interseccion.
  - Verificar: `python devtools/run.py serverless tests --type=unit
    --module=devtools` (tests de dep_validator) verde.
- `devtools/tests/serverless/test_lint_deps_*.py`

### Modificar

- `devtools/serverless/flags.py` — agregar `lint-deps` a
  `VALID_COMMANDS`, su entrada en `_COMMAND_SUMMARIES`, `_COMMAND_FLAGS`.
  - Verificar: `serverless lint-deps --help` lista el comando.
- `devtools/serverless/main.py` — rutear `lint-deps` a `dep_validator`.
- `devtools/serverless/packaging.py` — `package_lambda` invoca el
  validador antes de instalar deps; si hay duplicacion, lanza
  `PackagingError`.
  - Verificar: un Lambda con dep duplicada falla el `build`.
- `devtools/serverless/help.py` — documentar el comando nuevo.

## Definition of Done de la fase

- [ ] `serverless lint-deps` existe y detecta deps duplicadas (AC-7).
- [ ] `serverless lint-deps` pasa cuando no hay duplicacion (AC-8).
- [ ] El `deploy`/`build` falla si un Lambda tiene deps duplicadas.
- [ ] Tests unit del validador verdes, coverage >= 80%.
- [ ] Los 4 Lambdas pasan `lint-deps` tras las fases 2-4 (sin
      duplicacion residual).

[< 05 Config tooling](05-fase-config-tooling.md) | [Siguiente: 07 Peso artefacto >](07-fase-peso-artefacto.md)
