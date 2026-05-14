# Throttling fundamentals: token bucket algorithm

> Como funciona el throttling nativo de API Gateway. Niveles (account-level,
> stage-level, usage-plan-level). 429 Too Many Requests. Retry strategy.

[← Architecture](./01-architecture.md) | [README](./README.md) | [Siguiente: Rate-limit per-IP →](./03-rate-limit-per-ip.md)

## Token bucket algorithm (conceptual)

API Gateway usa token bucket para throttling. Visualizado:

```
Bucket capacity = BurstLimit (p. ej. 5000 tokens)
Tokens refill = RateLimit tokens/segundo (p. ej. 10000 tokens/seg)

Cuando llega un request:
  - Si hay tokens en el bucket: restar 1, dejar pasar
  - Si no hay tokens: devolver 429 Too Many Requests

Cada segundo, se agregan RateLimit tokens (hasta llenar el bucket).
```

Ejemplo: rate limit 10,000 req/s, burst 5,000.

```
t=0s:    bucket=5000 (lleno)
t=0.1s:  10 requests llegan → bucket=4990 (OK)
t=0.2s:  15000 requests llegan
         - Primeros 4990: OK, bucket=0
         - Resto 10010: 429 Too Many Requests
t=0.3s:  1 segundo paso, refill 10000 tokens
         bucket=10000 (capped al burst limit)
         1 request: OK, bucket=9999
```

**Punto clave**: El throttling es **best-effort**, no garantizado.
AWS puede permitir un poco mas para evitar jitter.

## Limites por defecto (account-level)

Por region, por account, en tu cuenta AWS:

- **Steady-state**: 10,000 requests/segundo
- **Burst**: 5,000 requests (pico maximo simultaneo)

Estos limites aplican a **TODOS los APIs en tu account en esa region**.
Si tienes 10 REST APIs, comparten ese pool de 10K RPS + 5K burst.

Para **aumentar** estos limites, contactar AWS Support:
- Free tier: no aplica aumento
- Business/Enterprise support: puedes pedir aumento a 40K RPS, 20K burst

Los limites increased son **permanentes** para tu account + region.

## Jerarquia de throttling (orden de aplicacion)

API Gateway aplica throttling en este orden. Si una capa rechaza, devuelve 429:

1. **Per-client throttling** (usage plan + API key)
   - Limites configurados por cliente especifico
   - Ejemplo: Cliente A max 1000 req/min, Cliente B max 500 req/min
   - Aplica solo si el request tiene API key valida

2. **Per-method/per-stage throttling**
   - Limites configurados por route/stage
   - Ejemplo: POST /contact max 3 req/min, GET /projects max 100 req/min
   - Aplica a TODOS sin distinguir

3. **Account-level throttling**
   - Limites de toda la cuenta en la region
   - Ejemplo: max 10K req/s total en us-east-1
   - Fallback si no hay limites especificos

4. **AWS Regional hard limits**
   - Limites inmovibles de AWS (infrastructure protection)
   - Raramente se alcanzan en produccion

```
Request llega
    |
    v
¿Tiene API key valida? 
    |--SI--> Comprobar per-client limit (usage plan)
    |        |--OK--> OK, continuar
    |        |--EXCEED--> 429 Too Many Requests
    |
    |--NO--> Comprobar per-method/stage limit
             |--OK--> OK, continuar
             |--EXCEED--> 429 Too Many Requests
    |
    v
Comprobar account-level limit
    |--OK--> Invocar Lambda
    |--EXCEED--> 429 Too Many Requests
```

En este portfolio (form publico sin API keys), los requests van directo
a capa 2 (per-method throttling) + capa 3 (account-level).

## Per-method y per-stage throttling

Configurar limites por ruta (p. ej. POST /contact vs POST /track):

**En SAM template**:
```yaml
Resources:
  MyApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      MethodSettings:
        - ResourcePath: /contact
          HttpMethod: POST
          ThrottleSettings:
            RateLimit: 3
            BurstLimit: 5
        - ResourcePath: /track
          HttpMethod: POST
          ThrottleSettings:
            RateLimit: 30
            BurstLimit: 60
```

O via AWS CLI:
```bash
aws apigateway update-stage \
  --rest-api-id abc123 \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/~1contact~1POST/throttling/rateLimit,value=3 \
    op=replace,path=/~1contact~1POST/throttling/burstLimit,value=5
```

**Limites nuestros**:
- `/contact`: 3 req/sec steady, 5 req burst (form contacto, super estricto)
- `/track`: 30 req/sec steady, 60 req burst (telemetria pixel, mas permisivo)
- `/validate-turnstile`: 30 req/sec steady, 60 req burst (validacion interna)

Nota: estos limites son **globales** (no per-IP). Para per-IP, necesitas WAF.

## 429 Too Many Requests response

Cuando se alcanza throttle, API Gateway devuelve:

```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 1

{
  "message": "Too Many Requests",
  "__type": "TooManyRequestsException"
}
```

Headers importantes:
- `Retry-After: N` — cliente debe esperar N segundos antes de reintentar
- `x-amzn-RateLimit-Limit` — limite configurado (ej. "3")
- `x-amzn-RateLimit-Remaining` — tokens restantes en el bucket
- `x-amzn-RateLimit-Reset` — timestamp cuando se resetea el bucket

## Retry strategy (cliente)

Cuando el cliente recibe 429, debe:

1. **Esperar el tiempo indicado en Retry-After header**
2. **Exponential backoff** si hay reintentos multiples
3. **NO intentar inmediatamente** (solo causara mas 429)

Ejemplo JavaScript:
```javascript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url, options)
    
    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '1')
      const waitTime = retryAfter * 1000 * Math.pow(2, i) // exponential backoff
      
      console.warn(`Rate limited. Waiting ${waitTime}ms before retry ${i+1}`)
      await new Promise(resolve => setTimeout(resolve, waitTime))
      continue
    }
    
    return response
  }
  throw new Error('Max retries exceeded')
}
```

## Cuotas diarias (quotas)

Ademas de throttling (rate/second), puedes definir **cuotas diarias** (quota/day):

**En usage plan**:
```yaml
Quota:
  Limit: 50       # max 50 requests/dia
  Period: DAY     # resetea a medianoche UTC
```

Una vez alcanzada la quota, el cliente no puede hacer mas requests ese dia.
Devuelve 429 con mensaje diferente: `QuotaExceededException`.

**Para este portfolio**:
- `/contact`: 50 requests/dia por IP (strict, form contacto)
- `/track`: 1000 requests/dia por IP (permisivo, telemetria)

Nota: las quotas en API Gateway son **globales** (no por IP).
Para quotas per-IP, necesitas DynamoDB + Lambda authorizer customizado.
Hoy asumimos que WAF + API Gateway es suficiente.

## Monitoring throttling

CloudWatch Metrics (builtin):
- `Count` — numero total de requests
- `4XXError` — requests rechazados por cliente
- `5XXError` — errores del backend
- `Latency` — latencia promedio
- `ThrottledRequests` — numero de 429 devueltos

Crear alarma si ThrottledRequests > threshold:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name api-throttle-high \
  --alarm-description "Alert if throttled requests exceed 10/min" \
  --metric-name ThrottledRequests \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:AlertTopic
```

## Common gotchas

### Gotcha 1: Burst no es request concurrentes

El burst limit NO significa "maximo de requests concurrentes en paralelo".
Significa "pico maximo permitido en 1 segundo sin que se agoten los tokens".

Si configuras burst=5 pero reciben 100 requests en paralelo, van a ser
throttled. El burst protege contra *spikes cortas*, no contra volumetria
sostenida.

### Gotcha 2: Rate limit es *requests por segundo*, no por minuto

A veces la confusion es: "3 requests/min" vs "3 requests/segundo".

En API Gateway:
- `RateLimit: 3` = 3 req/segundo = 180 req/minuto = 10.8K req/hora

Para throttle de 3 req/minuto, calcula: 3 / 60 = 0.05 req/s.
Pero API Gateway minimo es 1 req/s. No puedes configurar <1.

**Solucion**: usar WAF para limites sub-segundo (3 req/5min). Ver 03.

### Gotcha 3: Throttle global vs per-IP

API Gateway throttle es **global** (suma de todas las IPs).
WAF es **per-IP**.

Ejemplo: si configuras API Gateway 3 req/s, significa 3 req/s TOTAL
de TODAS las IPs. No 3 req/s por IP.

Para 3 req/s por IP, necesitas WAF.

### Gotcha 4: Usage plans solo si tienes API keys

Si no usas API keys en el cliente, las usage plans se aplican a nivel
de stage (global). Mejor usar request validators para rechazar invalidos
y WAF para rate-limit per-IP.

## Next steps

- [03-rate-limit-per-ip.md](./03-rate-limit-per-ip.md) — WAF rate-based rules (solucion per-IP)
- [04-usage-plans-api-keys.md](./04-usage-plans-api-keys.md) — usage plans (si necesitas clientes B2B)
- [08-monitoring-logs.md](./08-monitoring-logs.md) — CloudWatch + alarmas

Verificado a fecha 2026-05-13.
