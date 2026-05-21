"""
Powertools v3 Tracer (X-Ray).

Uso:
    from shared.observability.tracer import tracer

    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        with tracer.provider.in_subsegment('turnstile_verify'):
            ...

X-Ray habilitado via Globals.Function.Tracing: Active en template.yaml.
"""

from aws_lambda_powertools import Tracer

tracer = Tracer()
