# Cost Optimization y Pricing us-west-2 (Mayo 2026)

> Desglose de costos reales para las tablas contacts y tracking. Estimaciones basadas en volumen esperado.

## Pricing Actual us-west-2 (Verificado Mayo 2026)

| Recurso | Precio |
|---------|--------|
| Write (On-Demand) | $1.25 por 1M WRU |
| Read (On-Demand) | $0.25 por 1M RRU |
| Storage | $0.25 por GB/mes |
| PITR (Point-in-Time Recovery) | $0.20 por GB/mes |
| On-Demand Backup | $0.10 por GB |
| Streams (optional) | $0.02 por 100K records |
| Global Tables (optional) | 3x storage + write costs |

**Free Tier (siempre gratis, no 12 meses):**
- 25 GB almacenamiento
- 25 WCU + 25 RCU (Provisioned mode) = ~200M requests/mes
- 2.5M DynamoDB Streams reads

## Estimacion: Tabla Contacts

### Volumen

- **Items por mes:** 200
- **Tamaño item:** ~1.5 KB (fields: id, email, name, message, etc.)
- **Retencion:** Permanente (sin TTL)

### Cálculo Mensual

**Writes:**
- 200 items/mes × 1.5 KB = 300 KB
- Costo: ($1.25 / 1M) × 300 = **$0.000375/mes** (~0.04 centavos)

**Reads:**
- ~100 queries/mes (admin dashboard, checks de duplicados)
- ~0.1 KB por query = 10 KB
- Costo: ($0.25 / 1M) × 10 = **$0.0000025/mes** (negligible)

**Storage:**
- 200 items × 1.5 KB = 0.3 MB (negligible vs 25GB free)
- Costo: **$0/mes** (dentro de free tier)

**PITR (si habilitado):**
- 0.3 MB × $0.20 = **$0.00006/mes** (negligible)

**Total mensual: ~$0.00044/mes** (menos de 1/1000 de centavo)

## Estimacion: Tabla Tracking

### Volumen

- **Items por mes:** 15000 (250/dia, variable)
- **Tamaño item:** ~0.3 KB (session_id, page_id, url, timestamps)
- **Retencion:** 60 dias (TTL borra automaticamente)

### Cálculo Mensual

**Writes:**
- 15000 items × 0.3 KB = 4.5 KB
- Costo: ($1.25 / 1M) × 4500 = **$0.005625/mes** (media centavo)

**Reads:**
- ~5000 queries/mes (analytics, session reconstruction)
- ~0.1 KB = 500 KB
- Costo: ($0.25 / 1M) × 500 = **$0.000125/mes**

**Storage (con TTL):**
- 60 dias de retencion: 15000 items/mes × 60d / 30d = 30000 items max en tabla
- 30000 × 0.3 KB = 9 MB media (TTL borra, no crece indefinidamente)
- Pero 9 MB es negligible vs 25 GB free
- Costo: **$0/mes** (dentro de free tier)

**TTL (sin costo adicional):**
- Borra automático = **$0/mes**

**PITR (si habilitado):**
- 9 MB × $0.20 = **$0.0018/mes** (negligible)

**Total mensual: ~$0.0057/mes** (media centavo)

## Costo Total: Ambas Tablas

```
Contacts:      $0.00044/mes
Tracking:      $0.0057/mes
================================================
Total:         $0.006/mes    (~36 centavos/año)
```

**Conclusion:** DynamoDB para este portfolio cuesta MENOS QUE GRATIS (free tier cubre).

## Cuando Los Costos Crecerian

### Escenario 1: 10x Traffic (15K → 150K items/mes)

- Tracking writes: $1.25 × (45000/1M) = $0.05625/mes (+10x)
- Storage 60d: 90 MB = dentro de free tier aún
- **Total: ~$0.06/mes**

### Escenario 2: 100x Traffic + Dashboard con GSI

- Tracking writes × 2 (GSI): $0.5625/mes
- Contacts reads × 10 (analytics): $0.01/mes
- **Total: ~$0.57/mes** (aún trivial)

### Escenario 3: Datamart con 5 GSI + PITR

- Tabla grande: 1GB almacenamiento
- 5 GSI × storage: 5GB
- Writes × 6 (tabla + 5 GSI): $0.375/mes
- Storage (PITR): (1 + 5) × $0.25 = $1.50/mes
- PITR (1 + 5): (1 + 5) × $0.20 = $1.20/mes
- **Total: ~$3.1/mes**

**Aún barato para un side project.**

## Optimizaciones

### 1. Usar On-Demand (YA HECHO)

On-Demand es ~2x más caro que Provisioned si tienes tráfico predecible, pero:
- Escala automáticamente
- Sin sorpresas de throttling
- Para este volumen, diferencia es cents/mes

### 2. TTL para Tracking (YA HECHO)

TTL borra items automáticamente sin costo → ahorra 100% en storage a los 60 dias.

**Sin TTL:** 15000 × 12 meses × 0.3KB = 54 MB/año → $0.162 costo acumulativo
**Con TTL:** Items borrados en 60 dias → $0/mes almacenamiento

### 3. Projection en GSI (Si aplica)

Si agregas GSI en futuro, usa KEYS_ONLY (no ALL) → ahorra 50% en storage de índice.

### 4. Compresión de Strings Largos

Si `message` crece >2KB, comprimir con gzip:

```python
import gzip
import base64

# Antes de guardar
compressed = base64.b64encode(gzip.compress(message.encode())).decode()
item['message_compressed'] = compressed

# Al leer
decompressed = gzip.decompress(base64.b64decode(item['message_compressed'])).decode()
```

Ahorro: ~70% en storage para textos largos.

### 5. Sparse Attributes

No guardes campos NULL. DynamoDB no cobra por atributos que no existen:

```python
# INCORRECTO: Guardar company=None
{'id': '1', 'email': 'user@example.com', 'company': None}

# CORRECTO: Omitir campo
{'id': '1', 'email': 'user@example.com'}
```

Ahorro: ~5-10% por item si muchos campos opcionales.

## Alerta de Costos

Configurar CloudWatch alarm para evitar sorpresas:

```yaml
# En SAM template
CostAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: ConsumedWriteCapacityUnits
    Namespace: AWS/DynamoDB
    Statistic: Sum
    Period: 86400  # 1 dia
    EvaluationPeriods: 1
    Threshold: 100000000  # 100M WRU/dia = ~$125/dia
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref AlarmTopic
```

## Monitoring

```bash
# Ver metricas de uso (CLI)
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --dimensions Name=TableName,Value=portfolio-dev-contacts \
  --start-time 2026-05-01T00:00:00Z \
  --end-time 2026-05-31T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

## Paso Siguiente

- Seguridad: [09-security-best-practices.md](09-security-best-practices.md)
