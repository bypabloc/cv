---
title: Algoritmos de rate-limiting - Comparacion
description: Fixed window, sliding window log, sliding window weighted, token bucket, leaky bucket. Analisis de trade-offs.
status: stable
last-reviewed: 2026-05-14
---

# 02. Algoritmos de rate-limiting - Comparacion

> Comparacion de 5 algoritmos comunes para rate-limiting. Elegimos **sliding window
> WEIGHTED** por balance entre simplicidad, precision y costo DynamoDB.

[← Decision WAF](./01-why-not-waf.md) | [README](./README.md) | [Siguiente: Deep dive →](./02-sliding-window-weighted-deep-dive.md)

## 1. Fixed Window (rechazado)

### Como funciona

```
Ventana: 60 segundos
Limite: 3 requests

T=0s:   contador=0
T=10s:  contador=1 (request 1) ✓
T=20s:  contador=2 (request 2) ✓
T=30s:  contador=3 (request 3) ✓
T=40s:  contador=3 (request 4) → BLOCKED ✗
T=59s:  contador=3 (still blocked)
T=60s:  contador RESETS a 0  ← Thundering herd aqui
T=60.1s: contador=1 (request) ✓ (N Lambdas lanzan al mismo tiempo)
```

### Problema: Thundering herd (cache stampede)

Al cambiar la ventana (T=60s), TODAS las requests bloqueadas en los ultimos
milisegundos se desbloquean simultaneamente.

Si hay N Lambdas esperando reset, todas lanzan requests al mismo tiempo →
**2x el limite en <100ms** cuando se espera que respete el limite.

### Ventajas

- Simple: solo un contador por ventana
- Bajo costo DynamoDB: 1 GET + 1 UPDATE por request

### Desventajas

- **Thundering herd garantizado** (inutil para este caso)
- Precisión pobre (usuario pude hackear esperando reset)

### Veredicto: RECHAZADO ❌

---

## 2. Sliding Window Log (rechazado)

### Como funciona

```
Limite: 3 requests en 60s
Request 1: T=10s → almacenar timestamp
Request 2: T=20s → almacenar timestamp
Request 3: T=30s → almacenar timestamp
Request 4: T=40s → revisar todos los timestamps en [T=40s-60s, T=40s]
            → hay 3 dentro de la ventana → BLOCKED
Request 5: T=75s → revisar [T=75s-60s, T=75s] = [T=15s, T=75s]
            → solo T=20s, T=30s quedan (T=10s fuera) → 2 requests → ALLOW
```

### Implementacion DynamoDB

```python
item = {
    'bucket_key': '<ip>#<endpoint>',
    'timestamps': [10, 20, 30],  # lista de timestamps
}

# Check: contar timestamps en ventana
recent = [ts for ts in item['timestamps'] if ts > now - window_seconds]
if len(recent) >= limit:
    return BLOCKED
else:
    recent.append(now)
    item['timestamps'] = recent[-limit:]  # guardar ultimos N
```

### Ventajas

- **Precision perfecta**: sabe exactamente que timestamps hay
- Sin thundering herd: cada request es exactamente checkeado

### Desventajas

- **Storage explota**: almacenas lista de timestamps. Si hay 1M requests/dia,
  cada item `timestamps` puede tener 1M+ valores.
- **Write amplification**: cada request es un UPDATE (list append).
- **No atomic**: append a lista NO es operacion atomica en DynamoDB
  (requerria una transaccion costosa).

### Veredicto: RECHAZADO ❌

---

## 3. Sliding Window WEIGHTED (RECOMENDADO) ✓

### Como funciona

```
Ventana actual: window_start = (now // window_seconds) * window_seconds
Ventana anterior: prev_window_start = window_start - window_seconds

Item DynamoDB:
{
  'bucket_key': '<ip>#<endpoint>#<window_start>',
  'count': 5,              # requests en ventana actual
  'prev_count': 2,         # requests en ventana anterior
  'prev_window_start': ts, # cuando empezo ventana anterior
}

Calculo efectivo:
elapsed_in_current = now - window_start
weight = (window_seconds - elapsed_in_current) / window_seconds
effective_count = count + (prev_count * weight)

Ejemplo:
  window_seconds = 60
  now = 35s
  window_start = 0s
  elapsed_in_current = 35s
  weight = (60 - 35) / 60 = 25/60 = 0.417
  
  Si count=3, prev_count=2:
    effective = 3 + (2 * 0.417) = 3.83
  
  Si limit=3:
    3.83 >= 3 → BLOCKED (suavemente)
```

### Ventajas

| Ventaja | Explicacion |
|---------|-------------|
| **Precision buena** | No perfecta (sliding window log), pero muy mejor que fixed window. |
| **Thundering herd reducido** | Weight proporcional suaviza los picos al borde de ventana. |
| **Storage minimo** | Solo 2 items: current bucket + prev bucket. ~200 bytes por IP+endpoint. |
| **Atomic en DynamoDB** | Usa `SET count = count + 1` (UpdateItem atomic). Sin transacciones costosas. |
| **Escalable** | On-Demand puede manejar N IPs sin limite. |
| **Costo bajo** | 1 GET + 1 UPDATE = 2 WCU por request. ~$0.00125 per 1M requests. |
| **Granularidad flexible** | Ventana de 60s, 300s, etc. Configurable. |

### Desventajas

| Desventaja | Mitigacion |
|-----------|-----------|
| **No es perfecta** | Usar si "buena precision" es aceptable (es para rate-limit, no para billing exacto). |
| **Calculo en Lambda** | 1 division por request. Negligible latencia (<1ms). |
| **Bucket TTL eventual** | Items no se borran exactamente. Pueden quedar 48h. Pero: On-Demand no cobra storage <25GB. |

### Veredicto: ELEGIDO ✓

---

## 4. Token Bucket (alternativa)

### Como funciona

```
Bucket capacity: 10 tokens
Refill rate: 1 token per 10s

T=0s:   tokens=10, last_refill=0
T=15s:  tokens=10-1=9, last_refill=15s (request 1 usa 1 token)
T=25s:  refill: added_tokens = floor((25-15) / 10) = 1
        tokens=9+1=10, last_refill=25s
T=30s:  tokens=10-3=7 (request 2,3,4 usan 3 tokens)
T=35s:  refill: added = floor((35-25) / 10) = 1
        tokens=7+1=8, last_refill=35s
```

### Implementacion DynamoDB

```python
item = {
    'bucket_key': '<ip>',
    'tokens': 10,
    'last_refill': 25,  # Unix timestamp
}

# Check + refill
now = time.time()
refill_tokens = floor((now - item['last_refill']) / refill_interval)
item['tokens'] = min(item['tokens'] + refill_tokens, capacity)
item['last_refill'] = now

if item['tokens'] >= request_cost:
    item['tokens'] -= request_cost
    return ALLOW
else:
    return BLOCKED (+ dime cuanto esperar)
```

### Ventajas

| Ventaja | Explicacion |
|---------|-------------|
| **Burst handling** | Si tienes 10 tokens, puedes hacer 10 requests seguidos (burst). Despues re-fill lentamente. |
| **Precision buena** | Cuentas tokens exactos, no ventanas. |
| **Comunicar espera** | Puedes decirle al cliente: "retry after 5s" (tiempo para re-fill). |

### Desventajas

| Desventaja | Impacto |
|-----------|--------|
| **Requiere lock distribuido** | Si 2 Lambdas lanzan simultaneamente, ambas ven same `tokens` value → perdida de update. Necesitas ConditionExpression. |
| **Costo lock** | Mas WCU (UpdateItem con condition) que sliding window. |
| **Overkill para este caso** | Portfolio tiene bajo volumen. Token bucket es para high-frequency burst handling. |

### Veredicto: OVERKILL para este caso. ALTERNATIVA viable si necesitas burst. ⚠️

---

## 5. Leaky Bucket (rechazado)

### Como funciona

```
Queue capacity: 10 requests
Leak rate: 1 request per second

T=0s:   queue=[request1], leaked=0
T=1s:   queue=[], leaked=1
T=2s:   queue=[], leaked=1 (nothing came)
T=3s:   queue=[request2, request3], leaked=1 (2 requests llegan)
T=4s:   queue=[request3], leaked=2 (request2 leaked)
T=5s:   queue=[], leaked=3
```

### Problema

- **Igual de complejo que token bucket** (mismo lock distribuido)
- **Sin burst**: si llegas requests rapido, se quedan en queue esperando
  leak. No es util para APIs que necesitan latencia baja.
- **Overhead operacional**: mantener queue en DynamoDB es tedioso.

### Veredicto: RECHAZADO ❌

---

## Tabla resumen: Todos los algoritmos

| Algoritmo | Precision | Thundering Herd | Costo DynamoDB | Storage | Complejidad | Recomendacion |
|-----------|-----------|---|---|---|---|---|
| **Fixed Window** | Pobre | Si (GRAVE) | Muy bajo | Minimo | Muy simple | ❌ Evitar |
| **Sliding Window Log** | Perfecta | No | Muy alto | Alto (O(N)) | Simple | ❌ Storage explota |
| **Sliding Window Weighted** | Buena | No (suave) | Bajo | Minimo | Media | **✓ ELEGIDO** |
| **Token Bucket** | Buena | No | Medio (lock) | Bajo | Alta | ⚠️ Overkill si bajo volumen |
| **Leaky Bucket** | Excelente | No | Alto (lock + queue) | Medio | Muy alta | ❌ Innecesario |

## Por que Sliding Window WEIGHTED

Para este portfolio:

1. **Costo**: Bajo ($0/mes free tier)
2. **Precision**: Suficiente (no necesitas perfection)
3. **Simplicity**: Mas simple que token bucket
4. **Escalabilidad**: On-Demand cubre ilimitadamente
5. **Implementacion**: 1 GET + 1 UPDATE atomic (sin locks)

Siguiente: [Deep dive del algoritmo](./02-sliding-window-weighted-deep-dive.md)

---

**Verificado a**: 2026-05-14 (Arpit Bhayani sliding window blog, Oneuptime atomic counters blog, AWS resource counters article)

**Fuentes**:
- [Arpit Bhayani: Sliding Window Rate Limiting](https://arpitbhayani.me/blogs/sliding-window-ratelimiter/)
- [Oneuptime: Sliding Window Rate Limiting in Python](https://oneuptime.com/blog/post/2026-01-21-sliding-window-rate-limiting-python/view)
- [AWS: Implement resource counters with DynamoDB](https://aws.amazon.com/blogs/database/implement-resource-counters-with-amazon-dynamodb/)
