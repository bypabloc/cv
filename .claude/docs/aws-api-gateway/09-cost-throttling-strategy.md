# Cost y estrategia de defense in depth

> Pricing 2026 us-east-1. Estimado <$20/mes total. Defense in depth:
> WAF (capa 1) → API GW (capa 2) → Lambda (capa 3).

[← Monitoring](./08-monitoring-logs.md) | [README](./README.md)

## Pricing desglosado (Mayo 2026, us-east-1)

### REST API Gateway

- **Per-request**: $3.50 / 1 millon de requests
- **Data transfer out**: $0.09 / GB (first 1GB/month free)

Estimado 10K requests/mes:
- Requests: 10K * ($3.50 / 1M) = $0.000035/mes ≈ negligible
- Data: 10K * 200B = 2MB ≈ negligible
- **Subtotal API GW: <$0.01/mes**

### AWS WAF

- **Web ACL**: $5.00 / mes
- **Per-rule**: $1.00 / mes (tenemos 2 rules: /contact + /track)
- **Requests**: $0.60 / 1 millon requests

Estimado:
- Web ACL: $5.00
- 2 rate-based rules: $2.00
- 10K requests: $0.000006/mes ≈ negligible
- **Subtotal WAF: $7.00/mes**

### Lambda (3 functions)

- **Invocations**: $0.20 / 1 millon
- **Duration**: $0.0000166667 / GB-second (256 MB = 0.25 GB)
- **Free tier**: 1M invocations + 400K GB-seconds / mes

Para 10K requests:
- 10K invocations * $0.20 / 1M = $0.002 (dentro free tier)
- 10K * 0.2 seg * 0.25 GB = 500 GB-sec (dentro free tier)
- **Subtotal Lambda: $0.00 (free tier)**

### CloudWatch Logs

- **Ingestion**: $0.50 / GB
- **Storage**: $0.03 / GB / mes (con retention 30 dias)

Estimado 10K requests * 1KB log:
- Ingestion: 10MB = $0.005
- Storage: 10MB * 30 dias / 30 = ~$0.00015/mes
- **Subtotal CloudWatch: <$0.01/mes**

### DynamoDB (si usas contacts table)

- **Write**: $1.25 / 1M writes
- **Read**: $0.25 / 1M reads
- **Storage**: $0.25 / GB-month

Estimado (tabla pequeña, <100MB):
- 10K writes: $0.0000125
- Storage (100MB): $0.025
- **Subtotal DynamoDB: <$0.05/mes**

### Total monthly (estimado)

```
API Gateway:      <$0.01
WAF:              $7.00
Lambda:           $0.00 (free tier)
CloudWatch:       <$0.01
DynamoDB:         <$0.05
────────────────
TOTAL:            ~$7.06/mes
```

Con usage mucho mas alto (100K req/mes):
- WAF: $7.00 (fijo)
- Lambda: $0.00 (aun free tier)
- API GW + data: $0.35 + $0.02 = $0.37
- **Total: ~$7.37/mes**

**Conclusion**: El 98% del costo es WAF (es fijo, no por-request).

## Como ahorrar

### Opcion 1: Usa HTTP API en lugar de REST (NO recomendado aqui)

HTTP API es 71% mas barato ($1/M vs $3.50/M), pero PIERDES:
- Usage plans (necesitas para throttling global)
- Request validators (necesitas para JSON Schema)
- Response mapping (necesitas para CORS en errors)

Si no necesitaras WAF de todas formas, HTTP API ahorraría ~$0.04/mes.
Pero necesitas WAF igual, asi que total de todas formas ~$7/mes.

**Conclusion**: No vale la pena el ahorro de $0.04 por perder features.

### Opcion 2: Reduce WAF a 1 rule (combina endpoints)

Cambiar WAF a UNA sola rate-based rule que valide todo:

```yaml
RateBasedStatement:
  Limit: 10  # Minimo WAF permite
  AggregateKeyType: IP
```

Ahorro: $1/mes (menos una rule).
**Costo nuevo: ~$6/mes**.

Pero entonces no puedes tener throttles distintos por endpoint
(/contact 3 req/min vs /track 30 req/min). Todo seria 10 req/5min.

**Conclusion**: Vale la pena pagar $1 extra para diferenciar.

### Opcion 3: Elimina DynamoDB (almacena logs en S3 solo)

Si contactos no se almacenan en tabla (ej. se envian directo a email),
eliminas DynamoDB.

Ahorro: negligible (aun <$0.05/mes).

### Opcion 4: Aumenta WAF rate limit (menos bloqueos, mas volume)

Cambiar `/contact` de 3 req/5min a 10 req/5min:

Beneficio: legitimos usuarios con conexion lenta no se throttle tanto.
Costo: igual ($1/rule/mes).

**Conclusion**: Cambiar logica, mismo costo.

## Defense in depth strategy (multiples capas)

Nunca confies en UNA sola capa de proteccion. Arquitectura defensiva:

```
[Nivel 1: AWS WAF]
  Rate-based rule per-IP
  - Bloquea IPs que exceden 3 req/5min en /contact
  - Bloquea IPs que exceden 30 req/5min en /track
  - Costo: $7/mes
  - Latency: ~10ms adicional

  ↓ (si IP no bloqueada por WAF)

[Nivel 2: API Gateway Throttling]
  Global throttle por endpoint
  - /contact: 3 req/sec (180 req/min)
  - /track: 30 req/sec (1800 req/min)
  - Costo: incluido en API Gateway
  - Latency: <5ms
  - Protege contra: un cliente legitimo con bug que hace spam

  ↓ (si no throttleado)

[Nivel 3: Request Validators]
  JSON Schema validation
  - Rechaza requests invalidos (400)
  - Sin invocar Lambda
  - Costo: $0
  - Latency: <5ms
  - Protege contra: malformed requests, injection attacks

  ↓ (si pasa validacion)

[Nivel 4: Lambda Layer]
  Business logic validation + rate-limiting customizado
  - Rate-limit per-user en DynamoDB (ej. 10 emails/hora per email)
  - Rate-limit por originating domain si es formulario embebido
  - Costo: incluido en Lambda
  - Protege contra: usuarios recurrentes con mal behavior

  ↓ (si pasa todas validaciones)

[Nivel 5: Observabilidad]
  CloudWatch Logs + Alerts
  - Detecta patrones sospechosos (ej. spike de validation errors)
  - Alertas a DevOps para accion manual (ban IP, cambiar WAF rule)
```

### Ejemplo ataque: que sucede en cada capa

**Escenario**: Atacante desde IP 203.0.113.100 hace 100 requests/sec a /contact.

```
t=0s   IP 203.0.113.100 envia primer request
       ↓
       WAF: Cuenta request 1 en ventana 5-min (OK, <3 limit? NO, limit es 3/5min)
       ❌ WAF BLOQUEA, respuesta 429 en 10ms
       
       Costo: $0 (WAF rechaza, no invoca Lambda)
       Latency: 10ms
```

**Si WAF no estuviera**:
```
t=0s   IP 203.0.113.100 envia 100 requests simultaneos
       ↓
       API Gateway: Throttle limit es 3 req/sec (burst 5)
       ❌ Primeros 5 se aceptan (burst), resto se throttle
       Respuesta 429 con Retry-After
       
       Costo: 5 * $0.000003 = ~$0.000015 (casi nada)
       Latency: <5ms para rechazos
```

**Si API Gateway no estuviera**:
```
t=0s   100 requests valida pero llegan todos a Lambda
       ✅ Lambda se ejecutan, procesa todos
       
       Costo: 100 * $0.0000002 = $0.00002 (~$0.02 por ataque)
       Latency: 200ms+ (cold starts)
```

**Si no hubiera validacion**:
```
t=0s   Atacante envia requests con JSON invalido
       
       Sin validators: se invoca Lambda igual
       Lambda crashea o retorna 500
       
       Costo: 100 * $0.0000002 = $0.00002 + bad UX
       Latency: 200ms+
```

**Conclusion**: Cada capa detiene ~99% de los ataques *antes* de que
lleguen a la siguiente capa.

## Comparacion: arquitectura defensiva vs basica

| Metrica | Basica (sin WAF/validation) | Defensiva (con capas) |
|---------|------|-----------|
| Costo attack de 10K req/sec | $2 (Lambda) | $0.007 (WAF) |
| Latency para request invalido | 200ms | 5ms |
| Reputacion: responsable | Spammer | Clean |
| Monitoring requerido | Manual | Automatico alertas |
| Recovery time | Horas | Minutos (cambiar WAF rule) |

## Recomendaciones finales

Para este portfolio:
1. **Mantener WAF activado** ($7/mes). No es negociable. Es capa 1.
2. **Mantener 2 rate-based rules** ($1 extra). Diferencia entre /contact (estricto) y /track (permisivo).
3. **Mantener request validators** ($0). Rechaza invalidos en API GW.
4. **Mantener CloudWatch + alertas** (<$0.01). Detecta anomalias.
5. **Mantener Lambda layer validation** ($0). Extra per-user rate-limiting en Lambda.

Presupuesto: **$7/mes**.

Si en futuro crece a 1M requests/mes:
- WAF: aun $7/mes (fijo)
- Lambda: podria exceder free tier (~$5/mes)
- API GW: $3.50/mes
- Total: ~$15.50/mes (aceptable para backend de esa escala)

Verificado a fecha 2026-05-13.
