"""
Powertools v3 Metrics (CloudWatch EMF).

Uso:
    from shared.observability.metrics import MetricUnit, metrics

    @metrics.log_metrics
    def lambda_handler(event, context):
        metrics.add_metric(name='FormSubmitted', unit=MetricUnit.Count, value=1)

Tambien actua como portador de `MetricUnit` (de Powertools) para que los
`core/` de los services NO importen `from aws_lambda_powertools.metrics`
directo (contrato `.claude/rules/lambda-shared-imports.md`).

Namespace: leido de POWERTOOLS_METRICS_NAMESPACE env var (default 'Portfolio').
Free tier CloudWatch: 10 metricas custom gratis perpetuo.
"""

import os

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

__all__ = ['MetricUnit', 'metrics']

# Inicializar con namespace explicito (fallback 'Portfolio'). Powertools lee
# POWERTOOLS_METRICS_NAMESPACE pero solo durante la primera invocacion - si
# el env cambia despues del import el namespace ya esta fijado.
metrics = Metrics(
    namespace=os.environ.get('POWERTOOLS_METRICS_NAMESPACE', 'Portfolio')
)
