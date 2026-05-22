# 02 — Fase 1: Auditoria de imports

[< 01 Contexto](01-contexto-y-decision.md) | [Siguiente: 03 Mover logica >](03-fase-mover-logica-a-shared.md)

## Objetivo

Mapear, por cada `core/` de Lambda, que librerias externas importa
directo y cuales le llegan por el cierre transitivo de `shared/`. Es la
fase de EXPLORACION: no modifica codigo, produce el documento que las
fases 2-6 consumen.

## 4. Diagrama de flujo

N/A — fase de analisis, no altera flujos de control.

## 5. Diagrama ER

N/A — no hay cambios en datos.

## Auditoria preliminar (ya ejecutada en exploracion)

### Imports de `shared.*` por core/

| Lambda | Subpaquetes `shared` importados (directos) |
|--------|--------------------------------------------|
| `contact_form` | `http`, `rate_limit`, `core`, `observability`, `aws`, `dynamodb` |
| `db` | `db`, `observability` |
| `stream_processor` | `observability`, `db` |
| `tracking_pixel` | `core`, `rate_limit`, `http`, `observability`, `cache`, `dynamodb` |

### Imports de libs externas DIRECTOS en core/

| Lambda | Libs externas que el `core/` importa directo |
|--------|----------------------------------------------|
| `contact_form` | `aws_lambda_powertools`, `pydantic`, `boto3` |
| `db` | `aws_lambda_powertools`, `pydantic`, **`alembic`** |
| `stream_processor` | `aws_lambda_powertools`, `pydantic`, `boto3`, **`sqlalchemy`** |
| `tracking_pixel` | `aws_lambda_powertools`, `pydantic` |

### Diagnostico

- **`alembic` en `db/core/services/db_service.py`** y **`sqlalchemy` en
  `stream_processor/core/services/stream_service.py`** son las dos
  violaciones de dominio: libs que son responsabilidad de `shared.db`
  ejecutadas directo en el `core/`. -> Fase 2 las mueve.
- `aws_lambda_powertools`, `pydantic`, `boto3` aparecen en los `core/`
  pero TAMBIEN los traen `shared.observability` (`powertools`),
  `shared.aws` (`boto3`) y casi todos los subpaquetes (`pydantic`).
  Bajo la regla estricta D-3, el `pyproject.toml` del Lambda NO los
  declara si el cierre de `shared/` ya los aporta. La fase 1 debe
  CONFIRMAR esto leyendo el `[project.dependencies]` de cada subpaquete
  de `shared/` del cierre.

## 6. Tests requeridos

N/A — fase de analisis, sin codigo nuevo.

## 7. Archivos afectados

### Crear

- `docs/progress/explore_serverless_deps_audit.md` — matriz completa:
  por Lambda, libs directas del `core/` vs libs del cierre de `shared/`,
  y la lista derivada de (a) logica a mover, (b) deps a borrar de cada
  `pyproject.toml`.
  - Verificar: el documento lista, para los 4 Lambdas, cada lib
    clasificada como `core-only`, `shared-provided` o `ambas`.

## Procedimiento

1. Por cada subpaquete de `shared/` (`core`, `aws`, `observability`,
   `http`, `db`, `dynamodb`, `cache`, `rate_limit`): leer su
   `pyproject.toml` y registrar `[project.dependencies]`.
2. Por cada Lambda: resolver el cierre transitivo (reusar la logica de
   `shared_resolver.resolve_lambda_shared`) y unir las deps externas de
   ese cierre.
3. Por cada Lambda: escanear los imports externos directos de su `core/`
   (todo `import X` / `from X` donde `X` no es `shared`, ni stdlib, ni
   modulo propio del Lambda).
4. Cruzar: para cada lib del `core/`, marcar si esta en el cierre de
   `shared/`. Resultado por lib: `core-only` (declarar en el Lambda),
   `shared-provided` (NO declarar, regla D-3), `ambas` (NO declarar — la
   trae `shared`, regla estricta).
5. Identificar la logica de dominio a mover: todo uso de `alembic` y
   `sqlalchemy` en `core/services/`.

## Definition of Done de la fase

- [ ] `docs/progress/explore_serverless_deps_audit.md` existe y clasifica
      las libs de los 4 Lambdas.
- [ ] La lista de logica a mover a `shared/db` esta cerrada (que
      funciones, de que archivo, a que modulo de `shared/db`).
- [ ] La lista de deps a eliminar de cada `pyproject.toml` esta cerrada.

[< 01 Contexto](01-contexto-y-decision.md) | [Siguiente: 03 Mover logica >](03-fase-mover-logica-a-shared.md)
