---
title: Observability - CloudWatch, logs, X-Ray, alarms
description: Metricas custom, structured logs, X-Ray segments, dashboards CloudWatch.
status: stable
last-reviewed: 2026-05-14
---

# 07. Observability - Rate-Limit Monitoring

> CloudWatch metrics, structured logs con Powertools, X-Ray segments, dashboards, alarms.

[← Management CLI](./06-management-cli.md) | [README](./README.md) | [Siguiente: Anti-patterns →](./08-anti-patterns.md)

## CloudWatch Metrics Custom

Usar AWS Lambda Powertools para publicar metrics sin overhead.

```python
# rate_limit/check.py (integrar en RateLimiter)

from aws_lambda_powertools.metrics import Metrics, MetricUnit

metrics = Metrics()

class RateLimiter:
    def check_or_raise(self, ip: str, endpoint: str, ...):
        # ...
        
        try:
            # Rate-limit check
            result = self.bucket_checker.check_and_increment(...)
            
            if result['allowed']:
                metrics.add_metric(
                    name='RateLimitAllowed',
                    unit=MetricUnit.Count,
                    value=1,
                )
            else:
                metrics.add_metric(
                    name='RateLimitThrottled',
                    unit=MetricUnit.Count,
                    value=1,
                )
                raise RateLimitExceededError(...)
        
        except RateLimitExceededError:
            metrics.add_metric(
                name='RateLimitBlocked',
                unit=MetricUnit.Count,
                value=1,
            )
            raise
        
        except IPBlacklistedError:
            metrics.add_metric(
                name='RateLimitBlacklistedIP',
                unit=MetricUnit.Count,
                value=1,
            )
            raise
        
        metrics.flush()  # Enviar a CloudWatch
```

### Metricas disponibles

| Metrica | Descripcion | Unidad |
|---------|-------------|--------|
| `RateLimitAllowed` | Requests permitidos | Count |
| `RateLimitThrottled` | Requests permitidos pero cerca del limite | Count |
| `RateLimitBlocked` | Requests bloqueados por rate-limit | Count |
| `RateLimitBlacklistedIP` | Requests de IP en blacklist | Count |
| `AutoBlacklistTriggered` | Auto-blacklist activado (bot detectado) | Count |
| `RateLimitCheckLatency` | Latencia del check (incluye DynamoDB) | Milliseconds |

## Structured Logs

```python
# rate_limit/check.py

from aws_lambda_powertools import Logger

logger = Logger()

def check_or_raise(self, ip: str, endpoint: str, country: str | None = None, ...):
    logger.info(
        'Rate limit check',
        extra={
            'ip': ip,
            'endpoint': endpoint,
            'country': country,
            'turnstile_validated': turnstile_validated,
        }
    )
    
    try:
        # Whitelist check
        if self.rules.is_whitelisted(ip):
            logger.debug('IP whitelisted', extra={'ip': ip})
            return {'allowed': True}
        
        # Blacklist check
        if self.rules.is_blacklisted(ip):
            logger.warning(
                'IP blacklisted',
                extra={
                    'ip': ip,
                    'action': 'block',
                }
            )
            raise IPBlacklistedError()
        
        # Rate-limit check
        result = self.bucket_checker.check_and_increment(...)
        
        if not result['allowed']:
            logger.warning(
                'Rate limit exceeded',
                extra={
                    'ip': ip,
                    'endpoint': endpoint,
                    'effective_count': result['effective_count'],
                    'limit': rule['limit'],
                }
            )
        
        return result
    
    except Exception as e:
        logger.exception(
            'Rate limit check error',
            extra={
                'ip': ip,
                'endpoint': endpoint,
                'error': str(e),
            }
        )
        raise
```

### Ejemplo de log JSON (CloudWatch Insights)

```json
{
  "timestamp": "2026-05-14T10:30:45.123Z",
  "level": "WARNING",
  "message": "Rate limit exceeded",
  "ip": "203.0.113.99",
  "endpoint": "/contact",
  "effective_count": 3.2,
  "limit": 3,
  "aws_request_id": "abc-123-def",
  "function_name": "contact-form-prod"
}
```

## X-Ray Segments

```python
# Lambda handler

from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture('rate-limit-check')
def check_or_raise(self, ip: str, endpoint: str):
    # DynamoDB queries automaticamente trackeadas por X-Ray
    result = self.bucket_checker.check_and_increment(...)
    return result

def handler(event, context):
    xray_recorder.put_annotation('endpoint', '/contact')
    xray_recorder.put_annotation('ip', extract_ip(event))
    
    limiter = get_limiter()
    limiter.check_or_raise(...)  # Dentro de X-Ray capture
```

### Vista en X-Ray console

```
handler (entry)
  └─ rate-limit-check (subsegment)
     ├─ DynamoDB.GetItem (rules table)
     ├─ DynamoDB.GetItem (buckets table)
     └─ DynamoDB.UpdateItem (buckets table)
       └─ latency: 15ms
```

## CloudWatch Dashboard

```python
# devtools/rate_limit/dashboard.py

import boto3
import json

cloudwatch = boto3.client('cloudwatch')

dashboard_body = {
    'widgets': [
        {
            'type': 'metric',
            'properties': {
                'metrics': [
                    ['AWS/Lambda', 'RateLimitAllowed', {'stat': 'Sum'}],
                    ['...', 'RateLimitThrottled', {'stat': 'Sum'}],
                    ['...', 'RateLimitBlocked', {'stat': 'Sum'}],
                    ['...', 'AutoBlacklistTriggered', {'stat': 'Sum'}],
                ],
                'period': 60,
                'stat': 'Sum',
                'region': 'us-east-1',
                'title': 'Rate-Limit Overview',
            }
        },
        {
            'type': 'log',
            'properties': {
                'query': '''
                    fields @timestamp, ip, endpoint, effective_count, limit
                    | filter level = "WARNING"
                    | stats count() by endpoint
                ''',
                'region': 'us-east-1',
                'title': 'Rate-Limit Blocks by Endpoint',
            }
        },
        {
            'type': 'metric',
            'properties': {
                'metrics': [
                    ['AWS/Lambda', 'RateLimitCheckLatency'],
                ],
                'period': 60,
                'stat': 'Average',
                'region': 'us-east-1',
                'title': 'Check Latency (p50, p99)',
            }
        },
    ]
}

cloudwatch.put_dashboard(
    DashboardName='portfolio-rate-limit',
    DashboardBody=json.dumps(dashboard_body),
)
```

## Alarms criticas

### Alarm 1: AutoBlacklistTooHigh

Si auto-blacklist se activa >5 veces en 1 hora = posible ataque activo.

```python
cloudwatch.put_metric_alarm(
    AlarmName='RateLimitAutoBlacklistTooHigh',
    ComparisonOperator='GreaterThanThreshold',
    EvaluationPeriods=1,
    MetricName='AutoBlacklistTriggered',
    Namespace='AWS/Lambda',
    Period=3600,
    Statistic='Sum',
    Threshold=5,
    ActionsEnabled=True,
    AlarmActions=[
        'arn:aws:sns:us-east-1:ACCOUNT:alerts',
    ],
    TreatMissingData='notBreaching',
)
```

### Alarm 2: RateLimitBlocksAnomaly

Si rate-limit blocks suben >200% respecto a baseline.

```python
cloudwatch.put_metric_alarm(
    AlarmName='RateLimitBlocksAnomaly',
    Metrics=[
        {
            'Id': 'm1',
            'ReturnData': True,
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/Lambda',
                    'MetricName': 'RateLimitBlocked',
                },
                'Period': 300,
                'Stat': 'Sum',
            }
        },
        {
            'Id': 'm2',
            'ReturnData': False,
            'Expression': 'ANOMALY_DETECTION_BAND(m1, 2)',
        }
    ],
    EvaluationPeriods=1,
    ComparisonOperator='LessThanLowerOrGreaterThanUpperThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:ACCOUNT:alerts'],
)
```

### Alarm 3: DynamoDBThrottling

Si DynamoDB devuelve ProvisionedThroughputExceededException (unlikely con On-Demand, pero posible).

```python
cloudwatch.put_metric_alarm(
    AlarmName='RateLimitDynamoDBThrottle',
    MetricName='DynamoDBThrottling',
    Namespace='AWS/DynamoDB',
    Period=60,
    Statistic='Sum',
    Threshold=1,
    ComparisonOperator='GreaterThanOrEqualToThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:ACCOUNT:alerts'],
)
```

## CloudWatch Insights queries

### Top IPs bloqueadas (last 1h)

```sql
fields @timestamp, ip, endpoint
| filter level = "WARNING" and message like /Rate limit exceeded/
| stats count() as blocks by ip
| sort blocks desc
| limit 10
```

### Auto-blacklist triggers (timeline)

```sql
fields @timestamp, ip, reason
| filter message like /Auto-blacklist triggered/
| stats count() by bin(5m)
```

### Latencia del rate-limit check

```sql
fields @duration
| filter @message like /rate-limit-check/
| stats avg(@duration) as avg_ms, pct(@duration, 99) as p99_ms, max(@duration) as max_ms
```

## SNS Alerts

```python
# Configurar SNS topic para notificaciones

sns = boto3.client('sns')

topic_response = sns.create_topic(Name='portfolio-rate-limit-alerts')
topic_arn = topic_response['TopicArn']

# Suscribir email (requiere confirmacion)
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='admin@example.com',
)

# Usar topic_arn en alarmas (ver arriba)
```

## Debugging local

```bash
# Ver logs en local (con SAM)
sam local start-api

# En otra terminal, trigger Lambda
curl -X POST http://localhost:3000/contact

# Logs aparecen en console con Powertools formatting
```

---

**Verificado a**: 2026-05-14 (AWS Lambda Powertools 2.18+, CloudWatch Insights syntax 2026)

**Fuentes**:
- [AWS Lambda Powertools - Metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html)
- [AWS Lambda Powertools - Logger](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
- [CloudWatch Insights query syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
