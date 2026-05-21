"""
Powertools v3 Metrics (CloudWatch EMF).

Uso:
    from aws_lambda_powertools.metrics import MetricUnit
    from shared.metrics import metrics

    @metrics.log_metrics
    def lambda_handler(event, context):
        metrics.add_metric(name='FormSubmitted', unit=MetricUnit.Count, value=1)

Namespace: leido de POWERTOOLS_METRICS_NAMESPACE env var (default 'Portfolio').
Free tier CloudWatch: 10 metricas custom gratis perpetuo.
"""

import os

from aws_lambda_powertools import Metrics

# Inicializar con namespace explicito (fallback 'Portfolio'). Powertools lee
# POWERTOOLS_METRICS_NAMESPACE pero solo durante la primera invocacion - si
# el env cambia despues del import el namespace ya esta fijado.
metrics = Metrics(
    namespace=os.environ.get('POWERTOOLS_METRICS_NAMESPACE', 'Portfolio')
)
