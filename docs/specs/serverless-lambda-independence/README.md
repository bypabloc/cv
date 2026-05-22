# Independencia de los Lambdas del backend serverless

> Plan de refactorizacion: cada Lambda del backend serverless deja de
> depender del `.venv` y del workspace uv compartidos. Sus tests y su
> ejecucion local pasan a ser aislados (un `.venv` propio por Lambda),
> se elimina la duplicacion de dependencias entre cada Lambda y los
> subpaquetes de `shared/`, y el packaging gana control de peso del
> artefacto (warning + error contra los limites de AWS Lambda).

## Indice

| Documento | Cuando leer |
|-----------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto, problema, solucion, criterios de aceptacion (AC) |
| [02-fase-auditoria-imports.md](02-fase-auditoria-imports.md) | Auditoria de imports por core/ — base de las reglas de dedup |
| [03-fase-mover-logica-a-shared.md](03-fase-mover-logica-a-shared.md) | Mover logica de db_service / stream_service a shared/db |
| [04-fase-venv-aislado.md](04-fase-venv-aislado.md) | `uv sync` por Lambda, eliminar workspace, devtools cierre+venv |
| [05-fase-config-tooling.md](05-fase-config-tooling.md) | ruff/mypy/pytest/coverage propios por paquete |
| [06-fase-validacion-dedup.md](06-fase-validacion-dedup.md) | Validador automatico de deps duplicadas en devtools |
| [07-fase-peso-artefacto.md](07-fase-peso-artefacto.md) | Warning + error de peso del zip/descomprimido |
| [08-descomposicion.md](08-descomposicion.md) | Descomposicion en tareas atomicas (paralelizacion) |
| [09-commits.md](09-commits.md) | Listado de commits incrementales |
| [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) | git worktrees: base secuencial + fases worktree-safe |
| [11-verificacion-e2e.md](11-verificacion-e2e.md) | Verificacion E2E iterativa (fase final, gate del PR) |

## Reglas criticas del plan

- SIEMPRE TDD estricto (Red-Green-Refactor) para la logica que se mueve
  a `shared/db`: tests primero, en `lambda/shared/tests/`.
- SIEMPRE cada Lambda corre sus tests con SU `.venv` aislado
  (`<lambda>/.venv`), NUNCA con `serverless/.venv`.
- SIEMPRE `serverless tests` re-sincroniza el `.venv` del Lambda
  (`uv sync` siempre) — maxima fidelidad, cero drift pyproject vs venv.
- NUNCA el `core/` de un Lambda declara en su `pyproject.toml` una
  dependencia que ya le llega por el vendoring de `shared/` (regla
  estricta de dedup — ver decision D-3).
- NUNCA se commitea `<lambda>/.venv`, `build/`, `build.zip` ni
  `core/shared/` — todos efimeros, todos gitignored.
- El build FALLA (error) si el artefacto supera el limite de AWS
  Lambda; avisa (warning) al acercarse.

## Decisiones no reabribles

| ID | Decision |
|----|----------|
| D-1 | Cada Lambda tiene `.venv` aislado, gestionado con `uv sync` on-demand. Se elimina el `.venv` compartido del backend. |
| D-2 | Se elimina el workspace uv de `serverless/pyproject.toml`. Cada Lambda y cada subpaquete de `shared/` tiene su `pyproject.toml` + `uv.lock` independiente. |
| D-3 | Regla estricta de dedup: si una lib llega al Lambda por el cierre transitivo de `shared/`, el `pyproject.toml` del Lambda NO la declara. Riesgo asumido: ver 06. |
| D-4 | La logica de negocio que hoy usa libs de dominio de `shared` (Alembic en `db`, SQLAlchemy en `stream_processor`) se mueve a `shared/db`. Los `core/` quedan como orquestadores delgados. |
| D-5 | Tooling (ruff, mypy, pytest, coverage) se descentraliza: cada Lambda y cada subpaquete de `shared/` lleva su config en su `pyproject.toml`. |
| D-6 | El warning de peso reporta AMBAS cifras: zip comprimido (vs 50 MB) y descomprimido (vs 250 MB). El build falla al pasar cualquiera de los dos hard limits de AWS. |
| D-7 | `uv sync` siempre re-sincroniza (no on-demand cacheado): cada corrida de tests garantiza venv == pyproject. |

## Limites de AWS Lambda (fuente del peso — investigado 2026-05-22)

| Limite | Valor | Tipo |
|--------|-------|------|
| `.zip` subida directa (sin S3) | 50 MB comprimido | Hard limit, no ajustable |
| `.zip` via S3 | sin limite propio (lo acota el descomprimido) | — |
| Paquete descomprimido (codigo + deps + layers) | 250 MB | Hard limit, no ajustable |
| Imagen OCI de contenedor | 10 GB | Hard limit, no ajustable |

Fuente: `docs/progress/explore_aws_lambda_size_limits.md` (docs.aws.amazon.com,
consultado 2026-05-22). Umbrales del plan:

- WARNING: zip > 40 MB (80% de 50) o descomprimido > 200 MB (80% de 250).
- ERROR (build aborta): zip > 50 MB o descomprimido > 250 MB.

## Estado por fase

| Fase | Estado |
|------|--------|
| 1 — Auditoria de imports | done |
| 2 — Mover logica a shared/db + shared/lambda_kit | done |
| 3 — Venv aislado + eliminar workspace | done |
| 4 — Config de tooling descentralizada | done |
| 5 — Validador de dedup | done |
| 6 — Peso del artefacto | done |
| 7 — Verificacion E2E | done |

Implementado en `feature/serverless-lambda-independence` (14 commits,
C-1..C-15). Suite verde: 398 tests del backend (4 lambdas con `.venv`
aislado + shared) + 209 tests de devtools.

## Navegacion

Empezar por [01-contexto-y-decision.md](01-contexto-y-decision.md).
