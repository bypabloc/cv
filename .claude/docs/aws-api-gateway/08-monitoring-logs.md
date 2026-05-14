# Monitoring: CloudWatch Logs, X-Ray, metricas

> Observabilidad completa: access logs en JSON, distributed tracing, alertas
> para anomalias (429 anormal, latency spike, 5xx errors).

[← Deployment SAM](./07-deployment-sam.md) | [README](./README.md) | [Siguiente: Cost strategy →](./09-cost-throttling-strategy.md)

## Access logs (JSON format)

Cada request a API Gateway genera un access log. Configurar en SAM:

```yaml
PortfolioApi:
  Type: AWS::Serverless::Api
  Properties:
    AccessLogSetting:
      DestinationArn: !GetAtt ApiAccessLogGroup.Arn
      Format: >
        {
          "requestId":"$context.requestId",
          "ip":"$context.identity.sourceIp",
          "userAgent":"$context.identity.userAgent",
          "requestTime":"$context.requestTime",
          "httpMethod":"$context.httpMethod",
          "resourcePath":"$context.resourcePath",
          "queryString":"$context.queryString",
          "status":"$context.status",
          "responseLength":"$context.responseLength",
          "integrationLatency":"$context.integration.latency",
          "error":"$context.error.message",
          "error.code":"$context.error.messageString"
        }
```

Log resultante:
```json
{
  "requestId": "abc123def456",
  "ip": "203.0.113.42",
  "userAgent": "Mozilla/5.0...",
  "requestTime": "13/May/2026:14:30:45 +0000",
  "httpMethod": "POST",
  "resourcePath": "/contact",
  "queryString": "",
  "status": 200,
  "responseLength": 145,
  "integrationLatency": 234,
  "error": null,
  "error.code": null
}
```

## CloudWatch Log Group y retention

```yaml
ApiAccessLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: /aws/apigateway/portfolio/prod
    RetentionInDays: 30  # Guardar 30 dias, luego borrar (ahorra costo)
```

Retenciones recomendadas:
- `/aws/apigateway/*`: 30 dias (bajo volumen, bajo costo)
- `/aws/lambda/*`: 7-14 dias (mas verbose)
- Production errors: 90 dias (compliance)

## Cloudwatch Insights: queries

Ejemplo 1: Top 10 IPs con requests rechazados

```sql
fields @timestamp, ip, status, resourcePath, error
| filter status >= 400
| stats count() as rejected by ip
| sort rejected desc
| limit 10
```

Ejemplo 2: Latencia P99 por endpoint

```sql
fields @timestamp, resourcePath, integrationLatency
| filter resourcePath in ["/contact", "/track"]
| stats pct(integrationLatency, 99) as p99_latency by resourcePath
```

Ejemplo 3: Alertas de 429 (rate limited)

```sql
fields @timestamp, ip, status, resourcePath
| filter status = 429
| stats count() as throttled_count, count_distinct(ip) as unique_ips by resourcePath
```

Ejecutar en CloudWatch Logs Insights (console AWS):
1. Abrir CloudFormation → stack → Outputs → ApiAccessLogGroup
2. Click en log group → Logs Insights
3. Pegar query + Run

## X-Ray tracing (distributed)

Habilitar tracing en SAM:

```yaml
Globals:
  Function:
    Tracing: Active  # X-Ray active

PortfolioApi:
  Type: AWS::Serverless::Api
  Properties:
    TracingEnabled: true
```

Esto genera traces que muestran el camino completo:
```
Browser request
    ↓
[API Gateway] (entrada)
    ↓
[Lambda] (logica)
    ↓ DynamoDB
[DynamoDB Query] (almacenamiento)
    ↓
[Response] (201 Created)
```

Ver en AWS X-Ray console → Service Map.

Cada traza incluye:
- Response time (latency breakdown)
- Errores y excepciones
- Subsegmentos (calls a DynamoDB, calls a APIs externas)
- Metadata customizado

Agregar metadata en Lambda:

```python
import json
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    tracer.put_annotation(key='customer_type', value='contact_form')
    tracer.put_metadata(key='request_body', value=json.loads(event['body']))
    
    # ... logica
    
    return {'statusCode': 200, 'body': json.dumps({'ok': True})}
```

## CloudWatch Metrics

Metricas builtin:
- `Count` — total requests
- `4XXError` — client errors (400, 401, 403, 404, 429)
- `5XXError` — server errors (500, 503)
- `Latency` — respuesta time en ms (p50, p90, p99)
- `IntegrationLatency` — tiempo que Lambda tarda (excluyendo overhead de API GW)
- `ThrottledRequests` — requests rechazados por throttling (429)

Dashboard en CloudWatch:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name portfolio-api-metrics \
  --dashboard-body file://dashboard.json
```

`dashboard.json`:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "Count", {"stat": "Sum"}],
          [".", "4XXError", {"stat": "Sum"}],
          [".", "5XXError", {"stat": "Sum"}],
          [".", "ThrottledRequests", {"stat": "Sum"}],
          [".", "Latency", {"stat": "Average"}],
          [".", "Latency", {"stat": "p99"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Portfolio API Overview"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/WAFV2", "AllowedRequests", {"stat": "Sum"}],
          [".", "BlockedRequests", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "WAF Traffic"
      }
    }
  ]
}
```

## Alarmas recomendadas

### Alarma 1: Throttled requests anormal

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name portfolio-api-throttled \
  --alarm-description "Alert if throttled requests exceed 10 in 5 min" \
  --metric-name ThrottledRequests \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:AlertTopic
```

Interpretacion:
- Valores normales: 0-2 por 5 min (bots ocacionales)
- Anormal: >10 en 5 min (posible ataque volumetrico)
- Accion: Revisar CloudWatch Logs Insights para ver que IPs

### Alarma 2: 5xx errors

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name portfolio-api-errors \
  --alarm-description "Alert if 5xx errors > 1 in 5 min" \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:AlertTopic
```

Causa: Lambda crash, timeout, bad code deploy.

### Alarma 3: Latencia P99 spike

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name portfolio-api-latency-high \
  --alarm-description "Alert if p99 latency > 5 seconds" \
  --metric-name Latency \
  --namespace AWS/ApiGateway \
  --statistic Maximum \
  --period 60 \
  --threshold 5000 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:AlertTopic
```

Causa: Lambda cold start, DB query lenta, DDoS.

## Log retention y costo

CloudWatch Logs cuesta $0.50 per GB ingested.

Estimado este portfolio:
- 10K requests/mes * 1KB log por request = 10MB/mes = ~$0.005/mes
- Negligible

Pero configurar retention de 30 dias para no acumular historico infinito.

## Correlacion: logs + traces + metrics

Workflow de investigacion de error:

1. **CloudWatch Metrics** → ves spike de 5XXError
2. **Logs Insights** → queries para encontrar timestamps con errores
3. **X-Ray** → ver el trace detallado de uno de esos requests
4. **CloudWatch Logs** → expandir un log individual para ver contexto

Ejemplo:
```
Metrics: 5XXError spike a las 14:30:00
↓
Logs Insights: SELECT * | filter status = 500 | filter requestTime >= "14:30"
  → Resultado: 5 requests entre 14:30:02 y 14:30:08
↓
X-Ray: Click en un trace de esos requests
  → Ver que Lambda timeout a los 30s (OOM o query lenta)
↓
Lambda Logs: Ver errores en CloudWatch Logs del Lambda
  → "Out of Memory: Memory limit exceeded for function"
↓
Action: Aumentar memory de Lambda en SAM template
```

## Testing alertas

Para testear que las alertas funcionan:

```bash
# Forzar 5xx error enviando request invalido
curl -X POST https://api.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{"invalid":"payload"}'

# Despues de algunos minutos, alarma se debe disparar
aws cloudwatch describe-alarms \
  --alarm-names portfolio-api-errors \
  --region us-east-1 \
  --query 'MetricAlarms[0].StateValue'
# Esperado: ALARM
```

## Gotchas

### Gotcha 1: X-Ray sampling

X-Ray registra tracing de acuerdo a un sampling rate. Default:
- First request per second
- 5% of additional requests

Significa que si tienes 1000 req/s, X-Ray solo registra ~50 requests.
Para alto volumen, cambiar sampling:

```python
from aws_xray_sdk.core import xray_recorder

xray_recorder.configure(
    sampling=True,
    context_missing='LOG_ERROR',
    sampling_rules=[
        {
            'description': 'errors only',
            'service_name': '*',
            'http_method': '*',
            'url_path': '*',
            'host': '*',
            'fixed_target': 0,
            'rate': 0,
            'rules_version': 1
        },
        {
            'description': 'all errors',
            'service_name': '*',
            'http_method': '*',
            'url_path': '*',
            'host': '*',
            'fixed_target': 0,
            'rate': 1,
            'resource_arn': '*error*'
        }
    ]
)
```

Pero para este portfolio (volumen bajo), sampling default es OK.

### Gotcha 2: Log group no creado automaticamente

A veces API Gateway no crea el log group automaticamente. Crear manual:

```bash
aws logs create-log-group \
  --log-group-name /aws/apigateway/portfolio/prod \
  --region us-east-1
```

### Gotcha 3: Costo de logs en high-volume

Si de repente tienes volumetria masiva (ataque DDoS), CloudWatch Logs puede
costar significante. Limitar retention a 7 dias temporalmente:

```bash
aws logs put-retention-policy \
  --log-group-name /aws/apigateway/portfolio/prod \
  --retention-in-days 7 \
  --region us-east-1
```

## Next steps

- [09-cost-throttling-strategy.md](./09-cost-throttling-strategy.md) — pricing total estimado
- README → seleccionar otro capitulo segun necesidad

Verificado a fecha 2026-05-13.
