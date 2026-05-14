# Observability: logging, tracing, metrics

> CloudWatch Logs, X-Ray tracing, structured logging con Powertools,
> correlación de IDs, CloudWatch Alarms.

[← Anterior: IAM security](./06-iam-security.md) | [Siguiente: Cost optimization →](./08-cost-optimization-2026.md)

## CloudWatch Logs: retention y querying

Lambda escribe automáticamente a CloudWatch Logs. Grupo: `/aws/lambda/<function-name>`.

Politica de retention:

```yaml
LogGroupRetentionInDays:
  dev: 7
  prod: 30
```

SAM:

```yaml
Globals:
  Function:
    Environment:
      Variables:
        AWS_LOGS_LOG_RETENTION_DAYS: 7
```

Queries útiles en CloudWatch Logs Insights:

```sql
-- Errores en ultima hora
fields @timestamp, @message
| filter @message like /error|Error|ERROR/
| stats count() as error_count by @logStream

-- Latencias por function
fields @duration
| stats pct(@duration, 99) as p99, pct(@duration, 95) as p95

-- Correlation con X-Ray
fields @timestamp, aws_request_id
| filter aws_request_id = "abc-123"
```

## X-Ray tracing: segmentos y subsegmentos

X-Ray traza invocaciones y llamadas a AWS services. Habilitar:

```yaml
Globals:
  Function:
    TracingConfig:
      Mode: Active
```

Lambda crea automáticamente un **segment** (root) por invocación. Powertools
agrega **subsegments** para subcalls (DynamoDB, SES, HTTP).

Console: CloudWatch → X-Ray → Traces.

Anatomia de trace:

```
Invocation (segment root)
├─ Lambda init (subsegment)
├─ DynamoDB PutItem (subsegment AWS auto-instrumented)
├─ SES SendEmail (subsegment AWS auto-instrumented)
├─ Custom tracer.capture_dict (subsegment manual)
└─ End (total duration)
```

Con Powertools:

```python
from aws_lambda_powertools import Tracer

tracer = Tracer()

@tracer.capture_lambda_handler
def handler(event, context):
    tracer.put_annotation('env', 'prod')  # filtrable
    tracer.put_metadata('contact_id', 'abc123')  # searchable
    
    result = tracer.capture_dict(
        name='validate_form',
        func=validate_form,
        event
    )
```

## Structured logging: JSON output

Print plano:

```
2026-05-13 14:32:10,123 Starting contact form
2026-05-13 14:32:10,456 Form valid
2026-05-13 14:32:10,789 Email sent
```

JSON estructurado (Powertools):

```json
{
  "level": "INFO",
  "timestamp": "2026-05-13T14:32:10.123Z",
  "message": "Contact form received",
  "service": "contact-form",
  "aws_request_id": "abc-def-123",
  "email": "user@example.com",
  "function_name": "contact-form"
}
```

CloudWatch Logs Insights puede parsear JSON y queryar por campos.

Configuracion:

```python
from aws_lambda_powertools import Logger

logger = Logger(
    service='contact-form',
    level='INFO'  # or use env var POWERTOOLS_LOG_LEVEL
)

@logger.inject_lambda_context
def handler(event, context):
    logger.info('Contact received', extra={
        'email': event['email'],
        'service': event['service']
    })
    logger.error('Validation failed', exc_info=True)  # con traceback
```

## Correlación de IDs

X-Ray correlation ID disponible:

```python
import os
from aws_lambda_powertools import Logger

logger = Logger()

def handler(event, context):
    x_trace_id = os.environ.get('_X_AMZN_TRACE_ID')
    aws_request_id = context.aws_request_id
    
    logger.info('Starting', extra={
        'x_trace_id': x_trace_id,
        'request_id': aws_request_id
    })
```

Powertools automáticamente incluye `aws_request_id` en todos los logs:

```json
{
  "message": "Starting",
  "aws_request_id": "abc-123",
  "x_amzn_trace_id": "Root=1-xxx;Parent=yyy"
}
```

## CloudWatch Alarms

Alertar en:
- Error rate > 5% en 5 minutos
- Duration p99 > 2 segundos
- Throttles detectados

```yaml
ContactFormErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: contact-form-errors
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300  # 5 min
    EvaluationPeriods: 1
    Threshold: 5  # >5 errores en 5 min
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: !Ref ContactFormFunction
    AlarmActions:
      - !Ref SNSTopic

ContactFormDurationAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: contact-form-slow
    MetricName: Duration
    Namespace: AWS/Lambda
    Statistic: p99  # percentil 99
    Period: 300
    EvaluationPeriods: 2
    Threshold: 2000  # >2000ms
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: !Ref ContactFormFunction
    AlarmActions:
      - !Ref SNSTopic

SNSTopic:
  Type: AWS::SNS::Topic
  Properties:
    DisplayName: Portfolio Lambda Alerts
    TopicName: portfolio-lambda-alerts
```

## Custom metrics con Powertools

Emitir metricas a CloudWatch:

```python
from aws_lambda_powertools import Metrics

metrics = Metrics()

@metrics.log_cold_start_metric  # auto metric: cold start
def handler(event, context):
    metrics.add_metric(
        name='ContactProcessed',
        unit='Count',
        value=1
    )
    
    metrics.add_metadata(
        key='email',
        value=event['email']
    )
```

Output EMF (Embedded Metric Format) que CloudWatch parsea.

Query:

```sql
fields ContactProcessed
| stats sum(ContactProcessed) as total
```

## Log groups: configuracion SAM

```yaml
Resources:
  ContactFormLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/lambda/${ContactFormFunction}'
      RetentionInDays: 7

Outputs:
  LogGroupName:
    Value: !Ref ContactFormLogGroup
```

## Debugging: reproducer local con sam local

```bash
sam local invoke ContactFormFunction \
  -e events/contact.json \
  --debug

# Output incluye logs en stderr
```

O con environment variable para debug:

```bash
POWERTOOLS_LOG_LEVEL=DEBUG sam local invoke ContactFormFunction -e events/contact.json
```

## Best practices

1. **Always include correlation ID en logs**: aws_request_id es unico por invocation
2. **Structured logging**: JSON parseable, no strings planas
3. **No log sensitive data**: emails, IP addresses, form contents (si contiene PII)
4. **Use X-Ray annotations**: env, stage, service version
5. **Alarms on errors**: configurar SNS topic para alertas
6. **Retention policy**: 7d dev, 30d prod (cost optimization)

Verificado a fecha 2026-05-13.
