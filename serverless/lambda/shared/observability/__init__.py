"""
Subpaquete `observability`: logging y metrics (Powertools v3).

Agrupa las instancias module-scope de AWS Lambda Powertools: `logger`
(JSON estructurado) y `metrics` (CloudWatch EMF). Se configuran via env
vars (`POWERTOOLS_*`); las Lambdas las importan y las usan como
decoradores o directamente. X-Ray NO se usa en este backend (sin
`aws-xray-sdk`); ver `.claude/rules/lambda-config.md`.

Tambien re-exporta `MetricUnit` para que los `core/` de los services NO
importen `from aws_lambda_powertools.metrics import MetricUnit` directo
(ver `.claude/rules/lambda-shared-imports.md`).

Convencion: importar SIEMPRE desde `shared.observability` (o el modulo
correspondiente).
"""

from aws_lambda_powertools.metrics import MetricUnit
from shared.observability.logger import logger
from shared.observability.metrics import metrics

__all__ = [
    'MetricUnit',
    'logger',
    'metrics',
]
