# Fase D — shared.observability re-exporta MetricUnit

> shared.observability re-exporta `MetricUnit` de aws-lambda-powertools.
> Los services importan `from shared.observability import logger, metrics,
> tracer, MetricUnit` y nunca `from aws_lambda_powertools.metrics import MetricUnit`.

## Contexto / Problema

5 archivos en services importan `MetricUnit` directo:

- `cv/core/handler.py`
- `db/core/handler.py` (L39)
- `contact_form/core/services/contact_service.py` (L36)
- `tracking_pixel/core/handler.py`
- `stream_processor/core/handler.py` (L35)

Todos lo usan en llamadas `metrics.add_metric(name=..., unit=MetricUnit.Count,
value=1)`. Patron uniforme. `shared.observability` ya re-exporta `logger`,
`metrics`, `tracer`.

## Solucion

Editar `serverless/lambda/shared/observability/__init__.py`:

```python
from aws_lambda_powertools.metrics import MetricUnit
from shared.observability.logger import logger
from shared.observability.metrics import metrics
from shared.observability.tracer import tracer

__all__ = ['MetricUnit', 'logger', 'metrics', 'tracer']
```

NO se cambia nada en services aqui (Fase E).

## Archivos afectados

### Modificar

- `serverless/lambda/shared/observability/__init__.py` — agrega re-export de `MetricUnit`.
  - Verificar: `python -c "from shared.observability import MetricUnit; print(MetricUnit.Count)"`.

## Criterios de aceptacion

- **AC-D1**: Given la fase D aplicada, When importo `from shared.observability
  import MetricUnit`, Then importacion exitosa y `MetricUnit.Count` es el
  mismo objeto que `aws_lambda_powertools.metrics.MetricUnit.Count`.
- **AC-D2**: Given el `__all__` de shared.observability, When inspecciono,
  Then contiene `'MetricUnit'` ademas de `'logger', 'metrics', 'tracer'`.

## Verificacion

```bash
python -m compileall -q serverless/lambda/shared/observability

cd serverless/lambda && uv run python -c "
from aws_lambda_powertools.metrics import MetricUnit as APUnit
from shared.observability import MetricUnit
assert MetricUnit is APUnit, 'no es la misma clase'
print('OK')
"

python devtools/run.py serverless tests --type=unit --shared
```

## Commit

```text
feat(shared/observability): re-exporta MetricUnit de Powertools

- shared/observability/__init__.py: agrega MetricUnit al re-export y a
  __all__, junto a logger/metrics/tracer ya existentes
- Permite que los services hagan from shared.observability import
  MetricUnit en vez de from aws_lambda_powertools.metrics import MetricUnit
- Services migran sus imports en Fase E (5 archivos consumers)
```
