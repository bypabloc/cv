# Costos y pricing 2026

> Free tier, pricing estándar, estimaciones para contact-form / tracking-pixel,
> cost optimization strategies, DynamoDB on-demand, SES pricing.

[← Anterior: Observability](./07-observability.md) | [Siguiente: Alternatives →](./09-lambda-vs-alternatives.md)

## Free tier: nunca expira

AWS Lambda free tier es **perpetuo** (no expira después de 12 meses):

- **1 millón de requests/mes** (gratis siempre)
- **400,000 GB-segundos/mes** (gratis siempre)
- Data transfer: gratis dentro de AWS region

Para este proyecto (contact-form 100 req/mes, tracking-pixel 5000 req/mes):
- Total: ~5100 req/mes **dentro de free tier**

DynamoDB free tier también perpetuo:
- **25 RCUs + 25 WCUs** (gratis)
- **1 GB almacenamiento** (gratis)

Para contact-form (100 writes/mes) + tracking-pixel (5000 writes/mes):
- Total: ~5100 writes/mes **dentro de free tier**

SES **NO tiene free tier permanente** (0.10 per 1000 emails).

## Pricing on-demand (post free-tier)

| Servicio | Pricing |
|----------|---------|
| Lambda requests | $0.20 per 1M requests |
| Lambda compute | $0.0000166667 per GB-second (us-east-1) |
| DynamoDB write | $1.25 per 1M writes |
| DynamoDB read | $0.25 per 1M reads |
| SES | $0.10 per 1000 emails |
| CloudWatch Logs | $0.50 per GB ingested (desde May 2025) |
| X-Ray | $0.50 per 1M sampled traces |

## Estimacion para este proyecto

### Contact form (100 solicitudes/mes esperadas)

Handler: **512 MB memory**, **150ms duration**, **invokes SES + DynamoDB**.

```
Requests: 100/mes
Memory: 512 MB
Duration: 150 ms
GB-seconds: 100 * 0.512 * 0.15 / 3600 = 0.00213 GB-sec
```

**Dentro free tier (1M requests + 400k GB-sec)**: $0 /mes.

SES (1 email per submit): 100 emails/mes = $0.01/mes.

**Total contact-form: ~$0.01/mes**.

### Tracking pixel (5000 requests/mes esperadas)

Handler: **256 MB memory**, **50ms duration**, **solo DynamoDB**.

```
Requests: 5000/mes
Memory: 256 MB
Duration: 50 ms
GB-seconds: 5000 * 0.256 * 0.05 / 3600 = 0.0178 GB-sec
```

**Dentro free tier**: $0 /mes.

**Total tracking-pixel: $0/mes**.

### Resumen: <$1 USD/mes

```
Free tier
├─ Contact form: $0 (requests + compute)
├─ Tracking pixel: $0 (requests + compute)
├─ DynamoDB: $0 (all writes)
└─ SES: $0.01 (100 emails)
────────────────────
Total estimado: $0.01-$0.05/mes
```

**CRUCIAL**: este pricing asume **traffic bajo**. Si scaling dramatico (10k+
requests/dia), revisar cost.

## Cost optimization strategies

### 1. Usar arm64 en lugar de x86_64 (-20% cost)

```yaml
Architectures:
  - arm64
```

Ahorra 20% en compute. Compatible con boto3, requests, pydantic.

Estimacion: $0.005/mes si escala a post free-tier.

### 2. Right-size memory

Menos memory = menor costo pero más duration. Usar Lambda Power Tuning:

```bash
lambda-power-tuning \
  --function contact-form \
  --payload '{"httpMethod":"POST","body":"..."}' \
  --num-runs 10 \
  --from 256 --to 1024 --step 128
```

Resultado típico: 512 MB es optimal para Python + boto3 + API calls.

### 3. DynamoDB: on-demand vs provisioned

Hoy: **PAY_PER_REQUEST** (on-demand).

Pros: solo pagas por writes reales (5100/mes = free tier).
Cons: más caro si escala (1.25/1M).

Si escala >1M writes/mes: considerar **provisioned** (25 WCUs = ~$12/mes).

```yaml
BillingMode: PAY_PER_REQUEST  # Hoy (bajo trafico)
# Post-scale:
BillingMode: PROVISIONED
BillingModeConfig:
  WriteCapacityUnits: 25
  ReadCapacityUnits: 25
```

### 4. CloudWatch Logs retention

Retención corta = costo bajo.

```yaml
LogRetentionInDays:
  dev: 7
  prod: 30
```

7 dias: ~$0.05/mes (20GB logs)
30 dias: ~$0.20/mes (80GB logs)

Hoy: mantener 7d dev, 30d prod. Log aggregation a S3 para long-term.

### 5. SES: sender addresses

Verificar sender email para lower limit (SES sandbox):
- Sandbox: 200 emails/dia max, solo para verified recipients
- Production: unlimited

Si contact-form escala a 1000+ emails/mes, pedir production access (AWS review).

Cost: sigue siendo $0.10/1000 emails.

### 6. SnapStart cost-benefit

SnapStart: +15% memory (snapshot storage).

```
Sin SnapStart (300ms cold start):
  100 invokes/mes, cold starts ~10x/mes
  ~0.005 GB-sec/mes = $0
  
Con SnapStart (30ms cold start):
  Memory +15% = +0.076 GB-sec para snapshots
  Cost delta: ~$0.001/mes
```

**ROI negativo para bajo trafico**. Activar solo si cold start es crítico
(API requiere <100ms response).

### 7. Reserved Capacity (NO recomendado hoy)

Reserved concurrency: $0.015 per unit/hour ($11/mes por unit).

Provisioned concurrency: $0.0000041667 per instance/second.

**Hoy: no usar**. On-demand throttling es muy alto limit (1000 concurrent).

### 8. Database: TTL cleanup

DynamoDB TTL auto-elimina items expirados (free, eventual cleanup).

```yaml
TrackingPixelTable:
  TimeToLiveSpecification:
    AttributeName: ttl
    Enabled: true
```

Items con `ttl < current_unix_time` se borran (no cuentan para storage pricing).

## Cost breakdown: worst-case (post free-tier)

Si escala a 100k requests/mes:

```
Lambda requests: 100k * $0.20/1M = $0.02
Lambda compute: 100k * 0.256 * 0.05 / 3600 * $0.0000166667 = $0.02
DynamoDB writes: 100k * $1.25/1M = $0.125
SES emails: 1000 * $0.10/1000 = $0.10
CloudWatch Logs: 2GB * $0.50 = $1.00
X-Ray (10% sampled): 10k traces * $0.50/1M = $0.005
────────────────────
Total: ~$1.27/mes (still cheap)
```

Para escala 1M requests/mes:

```
Lambda: $0.20 + $0.20 = $0.40
DynamoDB: $1.25
SES: $1.00
CloudWatch: $5.00
X-Ray: $0.50
────────────────────
Total: ~$8.15/mes
```

## Monitoreo de costos

Activar AWS Cost Anomaly Detection:

```yaml
CostAnomalyDetector:
  Type: AWS::CE::AnomalyMonitor
  Properties:
    MonitorName: portfolio-anomaly
    MonitorType: DIMENSIONAL
    MonitorDimension: SERVICE
    MonitorFrequency: DAILY
```

Alertar si bill > expected threshold.

## Recomendaciones finales

1. **Hoy**: sin preocupacion por costo (free tier)
2. **Monitorear**: después de 3 meses, revisar metricas reales
3. **Escala**: si >100k requests/mes, evaluar:
   - SnapStart para cold start reduction
   - Arm64 para -20% cost
   - DynamoDB provisioned si trafico predecible
4. **SES**: pedir production access si >200 emails/dia

Verificado a fecha 2026-05-13 (pricing us-east-1, Mayo 2026).

Sources:
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Amazon DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)
- [Amazon SES Pricing](https://aws.amazon.com/ses/pricing/)
