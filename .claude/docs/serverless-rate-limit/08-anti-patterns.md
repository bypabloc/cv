---
title: Anti-patterns - Errores a evitar
description: 10 anti-patterns comunes en rate-limiting serverless.
status: stable
last-reviewed: 2026-05-14
---

# 08. Anti-patterns - Errores a evitar

> 10 errores comunes al implementar rate-limiting en serverless. Como evitarlos.

[← Observability](./07-observability.md) | [README](./README.md)

## 1. Usar Lambda Authorizer para rate-limit (❌ EVITAR)

### Problema

```
Lambda Authorizer es un middleware que ejecuta ANTES de la Lambda principal.
Parece ideal para rate-limit, pero:

1. Costo: cada Authorizer invocation = $0.000002 (paga invocaciones extra)
2. Latencia: adicional ~50-100ms
3. Cache complejo: autorizar y cachear respuesta requiere setup extra
4. No ve logica de negocio: no puede saber si Turnstile fue validado
```

### Caso de uso correcto

Lambda Authorizer es para **autenticacion** (JWT, OAuth), NO rate-limit.

### Implementacion CORRECTA

Rate-limit middleware DENTRO de la Lambda principal (primero en handler).

```python
def handler(event, context):
    # Paso 1: Rate-limit (dentro de Lambda, antes de logica)
    limiter = get_limiter()
    ip = event['requestContext']['identity']['sourceIp']
    
    try:
        limiter.check_or_raise(ip=ip, endpoint='/contact')
    except RateLimitExceededError:
        return {'statusCode': 429, 'body': '{"error": "Rate limit exceeded"}'}
    
    # Paso 2: Logica de negocio
    # ...
```

---

## 2. Fixed window (thundering herd)

### Problema

```
T=60s: ventana 1 (0-60) termina
  Rate: 3 req/min
  
A las T=60.0s:
  Lambda A: contador resetea a 0
  Lambda B: contador resetea a 0
  Lambda C: contador resetea a 0
  Lambda D: contador resetea a 0
  
Si 4 Lambdas lanzan al mismo tiempo → 4 requests en 100ms
→ Efectivamente: 4 x 3 req/min = 12 req en 100ms (✗ 4x el limite)
```

### Solucion

Usar **sliding window WEIGHTED** (ver [02-sliding-window-weighted-deep-dive.md](./02-sliding-window-weighted-deep-dive.md)).

---

## 3. Sin TTL en buckets de contadores

### Problema

```
Cada IP + endpoint + window_start = 1 bucket.

Con 100 requests/min + 10 IPs + 3 endpoints:
  ~30 buckets/min creados

Sin TTL:
  DynamoDB retiene indefinidamente
  Storage crece: 30 buckets/min x 60 minutos x 24h = 43,200 items/dia
  
Con TTL = window_seconds * 2 = 120s:
  Items vivos en DynamoDB = ~60s * 10 IPs * 3 endpoints = 1,800 items
  Storage: 1.8k items x 200 bytes = ~360 KB (perpetuo)
```

### Solucion

**SIEMPRE** setear `expires_at` con TTL = `window_seconds * 2` (buffer para edge cases).

```python
expires_at = now + (window_seconds * 2)
# En UpdateItem:
#   'expires_at = :expires_at'
#   ':expires_at': expires_at
```

---

## 4. Cachear contadores (CRITICO)

### Problema

```
Lambda A: GET bucket, vee counter=2
Lambda B: GET bucket, vee counter=2
Lambda A: ADD 1 → counter=3
Lambda B: CACHE (no vee el 3 que A escribio) → usa cached counter=2
Lambda B: ADD 1 → counter=3 (perdio el update de A)

Resultado: counter deberia ser 4, pero es 3 (lost update).
```

### Solucion

NUNCA cachear buckets (contadores). SIEMPRE READ fresh del DynamoDB.

Cachear SOLO rules (endpoint limits, IP whitelist, etc) que cambian raramente.

```python
# ✗ MAL
counter_cache = {}
def get_counter():
    if 'bucket' in counter_cache:
        return counter_cache['bucket']
    # ...

# ✓ BIEN
@cached(ttl=60)  # Cache RULES, not counters
def get_endpoint_rule(endpoint):
    return self.client.get_item('rules', {'rule_key': f'endpoint#{endpoint}'})

# Contadores: SIEMPRE fresh
bucket = self.client.get_item('buckets', {'bucket_key': bucket_key})
```

---

## 5. Lock distribuido para incrementar contador

### Problema

```
Algunos desarrolladores intentan usar locks explici:

def increment_counter(bucket_key):
    if acquire_lock(bucket_key):  # Toma lock
        counter = get_counter(bucket_key)
        counter += 1
        set_counter(bucket_key, counter)
        release_lock(bucket_key)
    else:
        wait_for_lock()  # Busy-wait
```

Problema: DynamoDB ADD es atomico, los locks son **innecesarios**.

```python
# ✓ MEJOR: UpdateItem con ADD (atomic)
table.update_item(
    Key={'bucket_key': bucket_key},
    UpdateExpression='SET current_count = if_not_exists(current_count, :zero) + :inc',
    ExpressionAttributeValues={':inc': 1, ':zero': 0},
)
```

---

## 6. Bloquear en sync con sleep

### Problema

```
Si rate-limit block, algunos intentan:

def check_rate_limit(ip):
    if exceeded:
        sleep(5)  # Esperar que se resetee
        retry()

Problema: Lambda corre en ~$0.0000002/100ms. Dormir 5s = desperdicio.
Costo: 50ms de wait = $0.000000001 (bajo pero antipatrón).
Mejor: rechazar rapido y dejar que cliente reintente.
```

### Solucion

```python
def check_or_raise(ip, endpoint):
    result = bucket_checker.check_and_increment(ip, endpoint)
    if not result['allowed']:
        raise RateLimitExceededError(retry_after=result['retry_after'])
    
    # No sleep, no wait. Rechazar rapido.
```

---

## 7. Usar X-Forwarded-For sin validacion

### Problema

```
Cliente malicioso puede spoofear IP:

curl -H "X-Forwarded-For: 1.1.1.1, 2.2.2.2, 3.3.3.3" \
     https://api.example.com/contact

El IP verdadero del cliente es escondido detras de false headers.

Si confias ciegamente en X-Forwarded-For, puedes:
  - Bloquear IPs innocentes
  - Permitir atacantes (si cambian su X-Forwarded-For)
```

### Solucion

**Prioridad de sources**:

```python
def extract_client_ip(event) -> str:
    """
    Extractar IP en este orden (por confiabilidad):
    1. CF-Connecting-IP (Cloudflare header, confiable)
    2. X-Forwarded-For (si Cloudflare) — primeros octet
    3. requestContext.identity.sourceIp (fallback)
    """
    
    headers = event.get('headers', {})
    
    # 1. Cloudflare (si existe)
    if 'cloudflare-ipaddress' in headers or 'cf-connecting-ip' in headers:
        return headers.get('cf-connecting-ip') or \
               headers.get('cloudflare-ipaddress')
    
    # 2. X-Forwarded-For si venimos de proxy conocido
    x_forwarded = headers.get('X-Forwarded-For', '')
    if x_forwarded:
        # Tomar solo el primer IP (cliente real)
        return x_forwarded.split(',')[0].strip()
    
    # 3. Fallback
    return event['requestContext']['identity']['sourceIp']
```

---

## 8. Rate-limit como UNICA defensa

### Problema

```
Rate-limit por IP es necesario pero INSUFICIENTE:

1. Distribuido DDoS: si atacante tiene 1000 IPs, rate-limit no ayuda
2. Slowloris: request lento que ocupa conexion sin contar contra limite
3. Amplification: atacante no es la IP que vemos
```

### Solucion (multi-layer)

```
Capa 1: Cloudflare upstream (edge, gratis, DDoS mitigation basico)
  ↓
Capa 2: Rate-limit per-IP en Lambda (este patron)
  ↓
Capa 3: Turnstile CAPTCHA (si flow lo permite)
  ↓
Capa 4: Reserved concurrency bajo (evita Lambda runaway)
  ↓
Capa 5: Manual blacklist (admin override)
```

Con todas las capas: defensa robusta.

---

## 9. Scan completo de buckets para stats

### Problema

```
Para ver stats, algunos hacen:

def get_stats():
    # ✗ MALO: Scan entire buckets table
    items = table.scan()
    
    blocked_count = 0
    for item in items:
        if item['current_count'] > limit:
            blocked_count += 1
    
    return blocked_count
```

Problema: DynamoDB Scan es **costoso**:
- Lee TODOS los items (puede ser 30k+)
- Consume RCU por cada item
- Tarda segundos (timeout posible)

### Solucion

Usar **CloudWatch Metrics** (ya publicadas por Powertools):

```python
# ✓ BIEN: Query CloudWatch Metrics
cloudwatch = boto3.client('cloudwatch')

response = cloudwatch.get_metric_statistics(
    Namespace='AWS/Lambda',
    MetricName='RateLimitBlocked',
    StartTime=datetime.now() - timedelta(hours=1),
    EndTime=datetime.now(),
    Period=60,
    Statistics=['Sum'],
)

blocked_count = sum([p['Sum'] for p in response['Datapoints']])
```

O CloudWatch Insights queries (ver [07-observability.md](./07-observability.md)).

---

## 10. Trust de auto-blacklist sin monitoring

### Problema

```
Auto-blacklist (3+ tokens Turnstile en 60s) es automatico.

Pero falsos positivos son posibles:
  - Usuario legit intento 3 veces rapido
  - Proxy residencial que cambia IP lentamente
  - Bug en Turnstile validation

Sin alarmas, usuarios get shadowbanned 24h sin notificacion.
```

### Solucion

```python
# 1. Alarm: si auto-blacklist > 5/h, avisar
cloudwatch.put_metric_alarm(
    AlarmName='AutoBlacklistTooHigh',
    MetricName='AutoBlacklistTriggered',
    Threshold=5,
    Period=3600,
    AlarmActions=[sns_topic],
)

# 2. Metric: track falsos positivos via manual unblock
# Admin puede desbloquear rapidamente via CLI

# 3. TTL 24h: recovery automatica (no permanent ban)

# 4. Monitor CloudWatch: ver que IPs se bloquean
# (ver [07-observability.md](./07-observability.md))
```

---

## Summary: Anti-patterns checklist

| Anti-pattern | Evitar | Hacer |
|---|---|---|
| Lambda Authorizer para rate-limit | ❌ | Middleware en Lambda principal |
| Fixed window | ❌ | Sliding window weighted |
| Sin TTL en buckets | ❌ | TTL = window_seconds * 2 |
| Cachear contadores | ❌ | Cachear solo rules, read fresh buckets |
| Lock distribuido para ADD | ❌ | DynamoDB atomic UpdateItem |
| Bloquear con sleep | ❌ | Rechazar rapido, cliente reintenta |
| Confiar solo X-Forwarded-For | ❌ | Priorizar CF-Connecting-IP |
| Rate-limit como unica defensa | ❌ | Multi-layer (CDN + rate-limit + CAPTCHA + concurrency) |
| Scan para stats | ❌ | CloudWatch Metrics o Insights |
| Auto-blacklist sin alarmas | ❌ | Alarmas + TTL 24h + CLI manual unblock |

---

**Verificado a**: 2026-05-14

**Fuentes**: Experiencias 2025-2026 en serverless rate-limiting, AWS best practices
