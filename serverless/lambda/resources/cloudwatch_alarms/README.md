# Catalogo de alarmas CloudWatch

Cada archivo `<short-name>.yaml` declara una alarma CloudWatch. devtools
las provisiona con `aws cloudwatch put-metric-alarm` (idempotente).

## Schema

```yaml
kind: cloudwatch-alarm

name: portfolio-<short>-${stage}
description: >
  Descripcion legible de cuando dispara y que accion tomar.

metric:
  namespace: AWS/Lambda                     # o AWS/ApiGateway, AWS/DynamoDB, etc
  name: Errors
  dimensions:
    FunctionName: portfolio-<X>-${stage}

threshold: 0
comparison: GreaterThanThreshold           # GreaterThanThreshold | LessThanThreshold | ...
evaluation_periods: 1
period_seconds: 300                        # 5 min
statistic: Maximum                         # Sum | Average | Maximum | Minimum
treat_missing_data: notBreaching           # opcional, default notBreaching

# SNS ARNs para notificar. Vacio = solo dashboard.
alarm_actions: []

tags: { Project: portfolio, ManagedBy: devtools }
```

## Convenciones

- `alarm_actions: []` por defecto (solo visible en el dashboard). Futuro:
  SNS topic para notificar por email/Slack.
- `treat_missing_data: notBreaching` evita falsos disparos cuando la
  metrica no se publica (ej. una funcion sin invocaciones en el periodo).

## Inventario actual

Sin alarmas. Las alarmas de DLQ SQS se eliminaron junto con SQS (el
backend usa invoke async Lambda->Lambda, ver el plan
serverless-sqs-to-async-invoke). El soporte `cloudwatch-alarm` se
mantiene en devtools para futuras alarmas (Lambda Errors, throttles,
API Gateway 5xx, etc.).
