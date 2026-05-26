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
  namespace: AWS/SQS                       # o AWS/Lambda, AWS/ApiGateway, etc
  name: ApproximateNumberOfMessagesVisible
  dimensions:
    QueueName: portfolio-<X>-dlq-${stage}

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

- Una alarma por DLQ (dispara cuando hay mensajes que el worker no pudo
  procesar tras max_receive_count retries).
- `alarm_actions: []` por defecto (solo visible en el dashboard). Futuro:
  SNS topic para notificar por email/Slack.
- `treat_missing_data: notBreaching` para metricas SQS (default `missing`
  podria romper la alarma cuando la cola esta vacia y SQS no publica
  metricas).

## Inventario actual

| Archivo | Metrica | Threshold |
|---------|---------|-----------|
| `contact-form-dlq-alarm.yaml` | ApproximateNumberOfMessagesVisible (DLQ) | >0 por 5min |
| `tracking-events-dlq-alarm.yaml` | ApproximateNumberOfMessagesVisible (DLQ) | >0 por 5min |
