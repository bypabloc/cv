# Monitoring: reputation dashboard, metricas, CloudWatch alarms

> Como monitorear sender reputation, detectar problemas, y mantener
> account saludable.

## SES Reputation Dashboard (AWS Console)

Acceso: AWS SES Console (us-east-1) → Account dashboard → Reputation metrics

### Metricas principales

| Metrica | Interpretacion | Alerta |
|---------|----------------|--------|
| Send | Emails aceptados por SES | Baseline (informativo) |
| Bounce | Hard + Soft bounces | > 5% = review, > 10% = suspend |
| Complaint | Emails marcados spam | > 0.1% = suspend |
| Delivery | Emails entregados al ISP | Target: > 98% |
| Open Rate | Emails abiertos (con tracking) | Informativo |
| Click Rate | Clicks en links (con tracking) | Informativo |

### Account Status

Dashboard muestra estado:
- **Healthy** (verde): Todo normal
- **Under Review** (amarillo): Bounce rate > 5%
- **At Risk** (naranja): Complaint rate > 0.05%
- **Suspended** (rojo): Bounce > 10% o Complaint > 0.1%

## CloudWatch Metrics (automaticas)

SES publica automaticamente metricas a CloudWatch en namespace `AWS/SES`.

### Ver metricas en CloudWatch

```bash
# Listar metricas disponibles
aws cloudwatch list-metrics \
  --namespace AWS/SES \
  --region us-east-1

# Output (parcial):
# MetricName: Send, Bounce, Complaint, Delivery, Open, Click
# Dimensions: Configuration Set (opcional), Source (optional)
```

### Ejemplo: obtener bounce rate (ultimas 24h)

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/SES \
  --metric-name Reputation.BounceRate \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average \
  --region us-east-1

# Response:
# {
#   "Datapoints": [
#     {"Timestamp": "2026-05-13T10:00:00Z", "Average": 2.5}
#   ]
# }
# Bounce rate promedio: 2.5% (HEALTHY)
```

## CloudWatch Alarms (alertas automaticas)

Configurar alarms para notificaciones cuando rates suben:

### Crear alarm: bounce rate

```python
import boto3

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

cloudwatch.put_metric_alarm(
    AlarmName='SES-BounceRate-High',
    MetricName='Reputation.BounceRate',
    Namespace='AWS/SES',
    Statistic='Average',
    Period=3600,  # 1 hora
    EvaluationPeriods=1,  # Evaluar 1 periodo consecutivo
    Threshold=3.0,  # 3% (conservative, AWS legal limit 5%)
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456:alerts'],
    AlarmDescription='Alert if SES bounce rate exceeds 3%',
    TreatMissingData='notBreaching',  # No alertar si no hay data
)
```

### Crear alarm: complaint rate

```python
cloudwatch.put_metric_alarm(
    AlarmName='SES-ComplaintRate-High',
    MetricName='Reputation.ComplaintRate',
    Namespace='AWS/SES',
    Statistic='Average',
    Period=3600,  # 1 hora
    EvaluationPeriods=1,
    Threshold=0.05,  # 0.05% (aggressive, AWS legal limit 0.1%)
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456:alerts'],
    AlarmDescription='Alert if SES complaint rate exceeds 0.05%',
    TreatMissingData='notBreaching',
)
```

### Crear alarm: send attempts

```python
cloudwatch.put_metric_alarm(
    AlarmName='SES-Send-Low',
    MetricName='Send',
    Namespace='AWS/SES',
    Statistic='Sum',
    Period=86400,  # 24 horas
    EvaluationPeriods=1,
    Threshold=0,  # 0 emails en 24h (para detectar silencio)
    ComparisonOperator='LessThanOrEqualToThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456:alerts'],
    AlarmDescription='Alert if no emails sent in 24h (possible Lambda failure)',
)
```

## SNS Topic para alertas

Configurar SNS para recibir notificaciones de alarmas:

```bash
# Crear SNS topic
aws sns create-topic \
  --name ses-alerts \
  --region us-east-1

# Output:
# TopicArn: arn:aws:sns:us-east-1:123456:ses-alerts

# Subscribir email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456:ses-alerts \
  --protocol email \
  --notification-endpoint pacg1991@gmail.com \
  --region us-east-1

# Confirmar subscription (click link en email)
```

## Dashboard personalizado (CloudWatch)

Crear dashboard para visualizar todas las metricas:

```python
import boto3
import json

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

cloudwatch.put_dashboard(
    DashboardName='SES-Reputation',
    DashboardBody=json.dumps({
        'widgets': [
            {
                'type': 'metric',
                'properties': {
                    'metrics': [
                        ['AWS/SES', 'Send', {'stat': 'Sum'}],
                        ['AWS/SES', 'Bounce', {'stat': 'Sum'}],
                        ['AWS/SES', 'Complaint', {'stat': 'Sum'}],
                        ['AWS/SES', 'Delivery', {'stat': 'Sum'}],
                    ],
                    'period': 3600,
                    'stat': 'Sum',
                    'region': 'us-east-1',
                    'title': 'Email Delivery Overview',
                },
            },
            {
                'type': 'metric',
                'properties': {
                    'metrics': [
                        ['AWS/SES', 'Reputation.BounceRate', {'stat': 'Average'}],
                        ['AWS/SES', 'Reputation.ComplaintRate', {'stat': 'Average'}],
                    ],
                    'period': 3600,
                    'stat': 'Average',
                    'region': 'us-east-1',
                    'title': 'Bounce & Complaint Rates',
                    'yAxis': {'left': {'min': 0, 'max': 10}},
                },
            },
        ],
    }),
)

print('Dashboard created: SES-Reputation')
```

## Mejores practicas de monitoreo

### 1. Check weekly (revisar cada semana)

```bash
# CLI command para resumen semanal
aws sesv2 get-account \
  --region us-east-1 \
  --query 'Account.[ReputationMetricsEnabled,SendingQuotaPercentage]'

# Response:
# [true, 0.001]  # 0.001% de quota usada (muy bajo)
```

### 2. Configurar dashboard local

Crear script Python que scrape metricas:

```python
import boto3
import json
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

def get_ses_metrics():
    """Obtiene metricas SES de ultimas 24 horas."""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)

    metrics = {}

    for metric in ['Send', 'Bounce', 'Complaint', 'Delivery']:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/SES',
            MetricName=metric,
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum', 'Average'],
        )
        metrics[metric] = response['Datapoints']

    return metrics


# Ejecutar
metrics = get_ses_metrics()
print(json.dumps(metrics, indent=2, default=str))
```

### 3. Responder a alertas

Cuando recibes alarma:

| Alarma | Causa probable | Accion inmediata |
|--------|---|---|
| BounceRate > 3% | Lista sucia, scraped emails | Revisar últimos 100 bounces. Limpiar list. |
| ComplaintRate > 0.05% | Spam perception, unwanted emails | Revisar subject lines. Agregar unsubscribe link. |
| Send = 0 (24h) | Lambda/SES error, no form submissions | Check CloudWatch Logs de Lambda. Revisar SES status. |
| Delivery < 90% | ISP rejections, authentication issue | Verificar DKIM/SPF/DMARC en Cloudflare. |

## Para este portfolio (bajo volumen)

Monitoreo minimalista (suficiente para 200 emails/mes):

1. **No necesita alertas criticas**: solo 1 recipient (owner)
2. **Revisar dashboard manualmente 1x/mes**: asegurar no hay bounces
3. **Habilitar account-level suppression**: auto-handle bounces
4. **No necesita SNS/Lambda**: bajo riesgo

```bash
# Monthly check (por email o calendario)
aws cloudwatch get-metric-statistics \
  --namespace AWS/SES \
  --metric-name Reputation.BounceRate \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average \
  --region us-east-1
```

Expected output:
```
Bounce rate: 0% (perfecto)
Complaint rate: 0% (perfecto)
Delivery rate: 100% (perfecto)
```

## Troubleshooting

### Bounce rate sube a 5%

**Causas**:
- Cambio en lista de recipients
- Validacion incompleta en form
- Email typos en form

**Solucion**:
1. Revisar logs de Lambda (que emails fallaron)
2. Revisar bounced recipient addresses
3. Mejorar validacion de email en form (regex + confirmation)

### Complaint rate > 0.1%

**Causas**:
- Emails no solicitados (spam perception)
- Demasiada frecuencia
- Subject line engañoso

**Solucion**:
1. Parar de enviar temporalmente
2. Revisar AWS Support case (puede ser false positive)
3. Cambiar texto de email o subject

### Account suspended

**Si pasa**:
1. Contact AWS Support immediately
2. Mostrar logs de validation
3. Mostrar suppression list cleanup (removi bounced addresses)
4. Solicitar lift de suspension

## Fuentes

- [AWS SES: Monitoring Sender Reputation](https://docs.aws.amazon.com/ses/latest/dg/monitor-sender-reputation.html)
- [AWS SES: Reputation Dashboard](https://docs.aws.amazon.com/ses/latest/dg/reputation-dashboard-dg.html)
- [AWS CloudWatch: User Guide](https://docs.aws.amazon.com/cloudwatch/)
- [boto3 CloudWatch API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html)

**Verificado 2026-05-13**
