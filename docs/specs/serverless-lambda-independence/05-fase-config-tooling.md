# 05 — Fase 4: Config de tooling descentralizada

[< 04 Venv aislado](04-fase-venv-aislado.md) | [Siguiente: 06 Validador dedup >](06-fase-validacion-dedup.md)

## Objetivo

`serverless/pyproject.toml` concentra hoy `[tool.ruff]`, `[tool.mypy]`,
`[tool.pytest.ini_options]`, `[tool.coverage]` y el grupo `dev`. Con los
Lambdas independientes, cada paquete (4 Lambdas + 8 subpaquetes de
`shared/`) lleva su config en SU `pyproject.toml`. El raiz queda minimo.

## 4. Diagrama de flujo

N/A — cambio de configuracion, no de flujo de control.

## 5. Diagrama ER

N/A.

## Que se mueve y a donde

| Bloque (hoy en `serverless/pyproject.toml`) | Destino |
|---------------------------------------------|---------|
| `[dependency-groups] dev` (pytest, moto, ruff, mypy, stubs) | El grupo `dev` de CADA `pyproject.toml` de Lambda + de cada subpaquete de `shared/` con tests. Solo las deps que ese paquete usa. NUNCA en `[project.dependencies]` (no van al zip). |
| `[tool.ruff]` + `[tool.ruff.lint]` + `[tool.ruff.format]` | Cada `pyproject.toml`. Mismo set de reglas. (Alternativa: un `ruff.toml` por paquete, como `devtools/ruff.toml`.) |
| `[tool.pytest.ini_options]` | Cada `pyproject.toml`. El `testpaths`/`addopts` apunta a los tests de ESE paquete. |
| `[tool.coverage.run]` + `[tool.coverage.report]` | Cada `pyproject.toml`. `source` y `omit` propios del paquete. |
| `[tool.mypy]` | Cada `pyproject.toml`. `files` propios del paquete. |

> `--cov-config` en `lambda_controller.py` apunta hoy a
> `serverless/pyproject.toml`. Tras el refactor cada comando de tests
> usa la config del `pyproject.toml` DEL paquete bajo test (Lambda o
> subpaquete). `lambda_controller.py` se ajusta para resolver el
> `--cov-config` correcto.

## Que queda en `serverless/pyproject.toml`

Decidir en la implementacion segun lo que reste:

- **Opcion A — archivo minimo**: solo metadata (`[project]` con `name`,
  `version`, `description`) como ancla del repo. Sin `[tool.*]`, sin
  `dependencies`.
- **Opcion B — eliminarlo**: si nada lo necesita (ni el CI, ni devtools,
  ni `uv`), se elimina. La raiz `serverless/` deja de tener
  `pyproject.toml`.

El plan prefiere **Opcion B** (coherente con "todo independiente"),
pero la fase debe verificar primero que ningun tooling externo
(`.github/workflows/`, hooks, `devtools/`) asume su existencia. Si algo
lo asume, se ajusta o se cae a Opcion A.

## Duplicacion aceptada

Descentralizar tooling DUPLICA la config de ruff/mypy/pytest entre 12
`pyproject.toml`. Es duplicacion ACEPTADA (Decision D-5): cada paquete
es autonomo, igual que `devtools/` tiene su `ruff.toml` autocontenido.
El trade-off es explicito — autonomia sobre DRY de configuracion.

## 6. Tests requeridos

### 6.B Unit / 6.C Typecheck

- No hay codigo nuevo: la verificacion es que `serverless lint`,
  `serverless typecheck` y `serverless tests` SIGUEN funcionando con la
  config descentralizada.
- Adaptar los tests de `devtools/serverless/` que asuman el
  `pyproject.toml` raiz como `--cov-config`.

## 7. Archivos afectados

### Modificar

- `serverless/lambda/services/<lambda>/pyproject.toml` (x4) — agregar
  `[dependency-groups] dev`, `[tool.ruff]`, `[tool.pytest.ini_options]`,
  `[tool.coverage.*]`, `[tool.mypy]`.
  - Verificar: `serverless tests --type=coverage --lambda=<x>` verde.
  - Verificar: `serverless lint --module=<x>` sin errores.
- `serverless/lambda/shared/<sub>/pyproject.toml` (x8) — agregar grupo
  `dev` + config de tooling (al menos los subpaquetes con tests).
  - Verificar: `serverless tests --type=coverage --shared=<sub>` verde.
- `devtools/serverless/lambda_controller.py` — `--cov-config` resuelve
  el `pyproject.toml` del paquete bajo test, no el raiz.
- `devtools/serverless/quality.py` — si asume el `pyproject.toml`/`ruff`
  raiz, ajustar a la config por paquete.

### Eliminar (o reducir a minimo)

- `serverless/pyproject.toml` — eliminar `[tool.*]` y
  `[dependency-groups]`. Opcion B: eliminar el archivo entero.
  - Verificar: `serverless lint` + `serverless typecheck` + `serverless
    tests` verdes sin el archivo (o con el minimo).

## Definition of Done de la fase

- [ ] Cada Lambda y cada subpaquete de `shared/` con tests tiene su
      config de ruff/mypy/pytest/coverage propia.
- [ ] `serverless/pyproject.toml` eliminado o reducido a metadata.
- [ ] `serverless lint`, `serverless typecheck`, `serverless tests`
      (`unit`/`coverage`) verdes con la config descentralizada.
- [ ] CI (`.github/workflows/`) sigue verde.

[< 04 Venv aislado](04-fase-venv-aislado.md) | [Siguiente: 06 Validador dedup >](06-fase-validacion-dedup.md)
