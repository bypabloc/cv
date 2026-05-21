"""
Subpaquete `observability`: logging, tracing y metrics (Powertools v3).

Agrupa las tres instancias module-scope de AWS Lambda Powertools:
`logger` (JSON estructurado), `tracer` (X-Ray) y `metrics` (CloudWatch
EMF). Se configuran via env vars (`POWERTOOLS_*`); las Lambdas las
importan y las usan como decoradores o directamente.

Convencion: importar SIEMPRE desde `shared.observability.<modulo>`.
"""

from shared.observability.logger import logger
from shared.observability.metrics import metrics
from shared.observability.tracer import tracer

__all__ = [
    'logger',
    'metrics',
    'tracer',
]
