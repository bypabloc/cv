"""
Powertools v3 Metrics (CloudWatch EMF).

Uso:
    from aws_lambda_powertools.metrics import MetricUnit
    from common.metrics import metrics

    @metrics.log_metrics
    def lambda_handler(event, context):
        metrics.add_metric(name='FormSubmitted', unit=MetricUnit.Count, value=1)

Namespace: 'Portfolio' (Globals.Function.Environment.POWERTOOLS_METRICS_NAMESPACE).
Free tier CloudWatch: 10 metricas custom gratis perpetuo.
"""

from aws_lambda_powertools import Metrics

metrics = Metrics()
