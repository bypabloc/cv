# 04 — Fase 3: Venv aislado por Lambda + eliminar workspace uv

[< 03 Mover logica](03-fase-mover-logica-a-shared.md) | [Siguiente: 05 Config tooling >](05-fase-config-tooling.md)

## Objetivo

Cada Lambda gana un `.venv` propio. Se elimina el workspace uv de
`serverless/pyproject.toml` y el `.venv` compartido. `run --stage=local`
(modo directo) y `tests` de cada Lambda usan SU `.venv`, no el del
backend.

## 4. Diagrama de flujo

### Antes

```text
serverless/pyproject.toml [tool.uv.workspace]
  -> serverless/.venv  (union de deps de los 4 Lambdas)
       ^-- run --stage=local (directo)  usa este
       ^-- tests --lambda=<x>           usa este
       ^-- tests --shared               usa este
```

### Despues

```text
serverless/lambda/services/<lambda>/
  pyproject.toml   (deps de runtime del Lambda + grupo dev)
  uv.lock          (lock independiente)
  .venv/           (gitignored, efimero)
       ^-- devtools: uv sync  +  uv pip install <deps del cierre shared>
       ^-- run --stage=local (directo) usa <lambda>/.venv
       ^-- tests --lambda=<x>          usa <lambda>/.venv

serverless/lambda/shared/<sub>/
  pyproject.toml + uv.lock + .venv/  (idem, para tests de shared)
```

## 5. Diagrama ER

N/A.

## Como entra al `.venv` del Lambda las deps de `shared/`

El `.venv` del Lambda solo tiene, por `uv sync`, las deps de SU
`pyproject.toml` (runtime + grupo dev). Pero al correr/testear, el
codigo importa `from shared.<sub>` y esos subpaquetes tienen sus propias
deps externas. Solucion (Decision: devtools resuelve el cierre):

1. devtools resuelve el cierre transitivo de `shared/` del Lambda
   (ya existe: `shared_resolver.resolve_lambda_shared` -> `(closure,
   external_deps)`).
2. devtools corre `uv sync` en `<lambda>/.venv` (deps del Lambda).
3. devtools corre `uv pip install <external_deps>` en ese mismo `.venv`
   para sumar las deps que aportan los subpaquetes de `shared/` del
   cierre.

El `pyproject.toml` del Lambda NO menciona `shared/` (regla D-3). El
`.venv` resultante refleja exactamente: runtime del Lambda + grupo dev +
deps del cierre de `shared/`.

`uv sync` se corre SIEMPRE antes de tests (Decision D-7): garantiza que
el `.venv` refleja el `pyproject.toml` y el `uv.lock` actuales.

## Nuevo modulo devtools: `serverless/venv.py`

Encapsula la gestion del `.venv` aislado:

- `ensure_lambda_venv(lambda_root) -> Path` — corre `uv sync` +
  `uv pip install` del cierre de `shared/`; devuelve el path del
  `python` del `.venv`.
- `ensure_shared_venv(subpackage_root) -> Path` — idem para un
  subpaquete de `shared/` (sus tests).
- Cache: `uv sync` es idempotente; correrlo siempre es barato si nada
  cambio. No se cachea manualmente.

`local_runtime.py` y `lambda_controller.py` dejan de apuntar a
`_PORTFOLIO_SERVERLESS_VENV` y usan `venv.ensure_lambda_venv(...)`.

## 6. Tests requeridos

### 6.A TDD flows (`serverless/venv.py`)

- `WHEN ensure_lambda_venv con un lambda que usa shared.db THEN el .venv
  resultante tiene sqlalchemy instalado [AC-2]`
- `WHEN ensure_lambda_venv THEN el python devuelto es <lambda>/.venv/bin/python [AC-2]`

### 6.B Unit tests (devtools, pytest)

- `devtools/tests/serverless/test_venv_*.py` — un archivo por escenario.
  Mockear `subprocess.run` (uv). Verificar el comando uv construido.
- Adaptar los tests de `local_runtime` y `lambda_controller` que hoy
  asumen `serverless/.venv`.

### 6.C Typecheck

- `mypy` del nuevo `venv.py` (corre en `devtools/.venv` 3.14).

## 7. Archivos afectados

### Crear

- `devtools/serverless/venv.py` — gestion del `.venv` aislado.
  - Verificar: `python devtools/run.py serverless tests --type=unit
    --module=devtools` (los tests de venv) verde.
- `devtools/tests/serverless/test_venv_*.py`
- `serverless/lambda/services/<lambda>/uv.lock` (x4) — generado por
  `uv lock` en cada Lambda.
  - Verificar: `uv sync --frozen` no falla en cada Lambda.
- `serverless/lambda/shared/<sub>/uv.lock` (x8) — idem para cada
  subpaquete de `shared/` (necesario para sus tests aislados).

### Modificar

- `serverless/pyproject.toml` — eliminar `[tool.uv.workspace]`,
  `[tool.uv.sources]`, las `dependencies` de workspace members. Ver
  fase 4 para que queda (o si se elimina).
  - Verificar: `rg 'tool.uv.workspace' serverless/pyproject.toml` vacio.
- `devtools/serverless/local_runtime.py` — `_run_direct` usa
  `venv.ensure_lambda_venv` en vez de `_PORTFOLIO_SERVERLESS_VENV`.
- `devtools/serverless/lambda_controller.py` — `_resolve_pytest_python`
  y `_run_shared_tests` usan el `.venv` aislado.
- `serverless/lambda/services/*/.gitignore` (x4) — agregar `.venv/`.
- `serverless/lambda/shared/*/.gitignore` o el `.gitignore` raiz —
  agregar `.venv/` para los subpaquetes.

### Eliminar

- `serverless/uv.lock` — el lock del workspace ya no aplica.
  - Verificar: `ls serverless/uv.lock` -> no existe.
- `serverless/.venv/` (efimero, no versionado — solo limpiar local).

## Riesgo y mitigacion

- **Riesgo**: la primera corrida de `serverless tests` sin target
  (4 Lambdas + shared) hace 5+ `uv sync`. Lento la primera vez.
  **Mitigacion**: `uv` cachea wheels globalmente; las corridas
  siguientes solo verifican el lock. Aceptado (Decision D-7).
- **Riesgo**: el modo RIE de `run-local` ya usa `package_lambda` (build
  arm64) — no se toca. Solo el modo `direct` cambia de `.venv`.

## Definition of Done de la fase

- [ ] `serverless/pyproject.toml` sin `[tool.uv.workspace]` (AC-1).
- [ ] `serverless/uv.lock` eliminado (AC-1).
- [ ] Cada Lambda tiene `pyproject.toml` + `uv.lock` + `.venv` propio.
- [ ] `serverless tests --type=unit --lambda=<x>` usa
      `<lambda>/.venv/bin/python` (AC-2).
- [ ] `serverless run --stage=local --runtime-mode=direct` de cada
      Lambda corre con su `.venv` aislado.
- [ ] `.venv/` gitignored en cada Lambda y subpaquete.

[< 03 Mover logica](03-fase-mover-logica-a-shared.md) | [Siguiente: 05 Config tooling >](05-fase-config-tooling.md)
