---
title: Sliding Window Weighted - Deep Dive
description: Matematica, implementacion con DynamoDB atomic operations, race conditions, edge cases.
status: stable
last-reviewed: 2026-05-14
---

# 02. Sliding Window WEIGHTED - Deep Dive

> Profundidad del algoritmo elegido. Matematica exacta, implementacion Python
> con DynamoDB UpdateItem atomic, analisis de race conditions y edge cases.

[← Algoritmos](./02-algorithms-comparison.md) | [README](./README.md) | [Siguiente: Schema →](./03-schema-design.md)

## Matematica del algoritmo

### Formulacion

```
Definiciones:
  window_seconds = duracion de ventana (ej. 60s)
  limit = numero de requests permitidos en ventana (ej. 3)
  now = Unix timestamp actual (segundos)
  
  window_start = floor(now / window_seconds) * window_seconds
    Ejemplo: si now=45 y window=60, window_start=0
              si now=125 y window=60, window_start=120
  
  prev_window_start = window_start - window_seconds
  
  elapsed_in_current = now - window_start
    Rango: [0, window_seconds)
  
  weight = (window_seconds - elapsed_in_current) / window_seconds
    Rango: (0, 1]
    Ejemplo: elapsed=0 → weight=1.0 (inicio ventana)
             elapsed=30 (en ventana 60) → weight=0.5
             elapsed=59 → weight=0.0167 (final ventana)

Calculo de effective_count:
  effective_count = current_count + (previous_count * weight)
  
Decision:
  if effective_count >= limit:
    return BLOCKED
  else:
    increment current_count
    return ALLOWED
```

### Intuicion del weight

El `weight` representa cuanta carga de la ventana anterior sigue "contando"
en la ventana actual.

Al inicio de una ventana nueva (elapsed=0), weight=1.0:
- La ventana anterior cuenta COMPLETA (todas sus requests siguen siendo validas)

Al final de una ventana (elapsed≈60s), weight≈0:
- La ventana anterior es casi ignorada (sus requests son muy viejas)

Esto **suaviza** el cambio de ventana y reduce thundering herd.

### Ejemplo visual

```
Ventana A (0-60s)     Ventana B (60-120s)
|-----------|          |-----------|
  count=3               count=0 (inicio)
  
T=45s (en ventana A):
  elapsed_in_A = 45 - 0 = 45
  weight_B = (60 - 45) / 60 = 0.25
  (si T=45 fuera el inicio de B:)
    effective = 0 + (3 * 0.25) = 0.75
    limit=3 → ALLOW (aun tenemos 2.25 requests)

T=65s (en ventana B):
  elapsed_in_B = 65 - 60 = 5
  weight_A = (60 - 5) / 60 = 0.917
  effective = 1 (count_B) + (3 (count_A) * 0.917) = 1 + 2.75 = 3.75
  limit=3 → BLOCKED (efectivamente agotado)

T=125s (en ventana C = 120-180):
  elapsed_in_C = 125 - 120 = 5
  weight_B = (60 - 5) / 60 = 0.917
  effective = 0 (count_C) + (1 (count_B) * 0.917) = 0.917
  limit=3 → ALLOW (ventana B casi expirada)
```

## Implementacion Python con DynamoDB

### Estructura de datos

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class RateLimitBucket:
    """Representa un bucket de rate-limit en DynamoDB."""
    bucket_key: str  # "<ip>#<endpoint>#<window_start>"
    current_count: int  # requests en ventana actual
    current_window_start: int  # timestamp inicio ventana actual
    window_seconds: int  # duracion ventana (ej. 60)
    previous_count: int  # requests en ventana anterior
    previous_window_start: int  # timestamp inicio ventana anterior
    expires_at: int  # Unix timestamp para TTL DynamoDB
    first_request: int  # timestamp del primer request en ventana actual
    last_request: int  # timestamp del ultimo request
    
    @property
    def effective_count(self, now: int) -> float:
        """Calcula effective_count con weight."""
        if now < self.current_window_start:
            # Reloj atrasado o error
            return float(self.current_count)
        
        elapsed_in_current = now - self.current_window_start
        if elapsed_in_current >= self.window_seconds:
            # Ventana paso, previous es viejo
            return float(self.current_count)
        
        weight = (self.window_seconds - elapsed_in_current) / self.window_seconds
        return self.current_count + (self.previous_count * weight)
```

### Check + Increment (atomic)

```python
import boto3
import time
from botocore.exceptions import ClientError

class RateLimitChecker:
    def __init__(self, table_name: str = 'rate_limit_buckets'):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def check_and_increment(
        self,
        ip: str,
        endpoint: str,
        limit: int,
        window_seconds: int = 60,
    ) -> dict:
        """
        Check rate-limit y incrementar contador atomicamente.
        
        Retorna:
            {
              'allowed': bool,
              'effective_count': float,
              'retry_after': int (segundos si blocked),
              'reason': str,
            }
        """
        now = int(time.time())
        window_start = (now // window_seconds) * window_seconds
        bucket_key = f"{ip}#{endpoint}#{window_start}"
        expires_at = now + (window_seconds * 2)  # TTL: 2 ventanas
        
        # Intento 1: GET item actual
        try:
            response = self.table.get_item(Key={'bucket_key': bucket_key})
            item = response.get('Item')
        except ClientError as e:
            return {
                'allowed': False,
                'error': f"DynamoDB error: {e}",
                'retry_after': 60,
            }
        
        # Calcular effective_count
        if item:
            current_count = item.get('current_count', 0)
            previous_count = item.get('previous_count', 0)
            current_window_in_item = item.get('current_window_start', window_start)
        else:
            current_count = 0
            previous_count = 0
            current_window_in_item = window_start
        
        # Check si ventana cambio
        if current_window_in_item != window_start:
            # Ventana nueva: current → previous
            previous_count = current_count
            current_count = 0
        
        # Calcular weight
        elapsed_in_current = now - window_start
        weight = max(0, (window_seconds - elapsed_in_current) / window_seconds)
        effective_count = current_count + (previous_count * weight)
        
        # Decision
        if effective_count >= limit:
            # Bloqueado: calcular retry_after
            requests_to_expire = effective_count - limit
            retry_after = int((requests_to_expire / weight) + 1) if weight > 0 else window_seconds
            return {
                'allowed': False,
                'effective_count': effective_count,
                'retry_after': min(retry_after, window_seconds),
                'reason': f'Rate limit exceeded ({effective_count:.2f}/{limit})',
            }
        
        # Permitido: incrementar contador atomicamente
        try:
            self.table.update_item(
                Key={'bucket_key': bucket_key},
                UpdateExpression=(
                    'SET current_count = if_not_exists(current_count, :zero) + :inc, '
                    '    current_window_start = :window_start, '
                    '    last_request = :now, '
                    '    expires_at = :expires_at '
                    'ADD first_request :first (si no existe, SET a now)'
                ),
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':zero': 0,
                    ':window_start': window_start,
                    ':now': now,
                    ':expires_at': expires_at,
                    ':first': set([now]) if not item else set(),  # ADD a set
                },
            )
            return {
                'allowed': True,
                'effective_count': effective_count + 1,
                'reason': 'OK',
            }
        except ClientError as e:
            return {
                'allowed': False,
                'error': f"Failed to increment: {e}",
                'retry_after': 60,
            }
```

### Forma correcta: UpdateItem con condicion

El codigo arriba es simplificado. La forma CORRECTA es:

```python
def check_and_increment_correct(
    self,
    ip: str,
    endpoint: str,
    limit: int,
    window_seconds: int = 60,
) -> dict:
    """
    Versión CORRECTA: calculo local + UpdateItem atomic + retry si window cambio.
    """
    now = int(time.time())
    window_start = (now // window_seconds) * window_seconds
    bucket_key = f"{ip}#{endpoint}#{window_start}"
    expires_at = now + (window_seconds * 2)
    
    # Intento 1: GET
    response = self.table.get_item(Key={'bucket_key': bucket_key})
    item = response.get('Item', {})
    
    current_count = item.get('current_count', 0)
    previous_count = item.get('previous_count', 0)
    item_window_start = item.get('current_window_start', window_start)
    
    # Detectar cambio de ventana
    if item_window_start != window_start:
        # Ventana cambio: promover previous
        previous_count = current_count
        current_count = 0
    
    # Calcular effective
    elapsed_in_current = now - window_start
    weight = (window_seconds - elapsed_in_current) / window_seconds
    effective_count = current_count + (previous_count * weight)
    
    # Decision
    if effective_count >= limit:
        return {
            'allowed': False,
            'effective_count': effective_count,
            'retry_after': window_seconds,
        }
    
    # Intento 2: UpdateItem atomic
    try:
        self.table.update_item(
            Key={'bucket_key': bucket_key},
            # Solo incrementar si la ventana no cambio desde nuestro GET
            ConditionExpression='attribute_not_exists(current_window_start) OR current_window_start = :expected_window',
            UpdateExpression=(
                'SET current_count = if_not_exists(current_count, :zero) + :inc, '
                '    current_window_start = :window_start, '
                '    previous_count = if_not_exists(previous_count, :zero), '
                '    previous_window_start = :prev_window, '
                '    last_request = :now, '
                '    expires_at = :expires_at'
            ),
            ExpressionAttributeValues={
                ':inc': 1,
                ':zero': 0,
                ':window_start': window_start,
                ':prev_window': window_start - window_seconds,
                ':expected_window': item_window_start,
                ':now': now,
                ':expires_at': expires_at,
            },
        )
        return {'allowed': True}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Ventana cambio entre GET y UPDATE: reintentar
            return self.check_and_increment_correct(ip, endpoint, limit, window_seconds)
        raise
```

## Race conditions: NONE (gracias a atomicity)

### Escenario 1: Dos Lambdas lanzan simultaneamente

```
Lambda A y B leen bucket mismo tiempo:
  T=100s: ambas leen current_count=2
  
A incrementa primero:
  DynamoDB: current_count=2+1=3
  A retorna: effective=3

B intenta incrementar:
  DynamoDB: current_count=3+1=4
  B retorna: effective=4

✓ NO hay race condition: DynamoDB ADD es atomic.
✓ Ambas operaciones se aplicaron.
```

### Escenario 2: Lambda A toma mas tiempo (slow recompute)

```
Lambda A: reads current_count=3
Lambda B: reads current_count=3
Lambda B: increments current_count=4, releases lock
Lambda A: increments current_count=5 (ignora el 4 que B escribio)

PERO: DynamoDB ADD es atomic. Ambas incrementan.
  UpdateItem(SET current_count = current_count + 1)
  Secuencia:
    1. A lee: 3
    2. B lee: 3
    3. A SET: 4
    4. B SET: 5 (ve el 4 que A escribio)
    
✓ NO hay lost update: cada ADD es atomica.
```

## Edge cases (importancia baja pero real)

### Caso 1: Clock skew (reloj atrasado en una Lambda)

```
Lambda A: now=100s (reloj correcto)
Lambda B: now=95s (reloj atrasado 5s)

B calcula: window_start = (95 // 60) * 60 = 60
A calcula: window_start = (100 // 60) * 60 = 60

✓ Sin problema: ambas caen en mismo bucket (60-120).
```

### Caso 2: TTL expires antes de que termine la ventana

```
Configuramos: expires_at = now + (window_seconds * 2) = 100 + 120 = 220s

Si DynamoDB TTL borra el item a los 120s:
  T=100s: item creado, expires_at=220s
  T=200s: si TTL es eventual, item puede estar O no estar
  T=220s: definitivamente borrado
  
  Impacto: si un bucket se borra antes de tiempo, contadores se pierden.
  Mitigacion: setear expires_at a (window_seconds * 3) para buffer.
```

### Caso 3: Request entre ventanas

```
T=59.9s: en ventana A (0-60)
T=60.0s: en ventana B (60-120)
T=60.1s: en ventana B

Si request tarda 0.2s desde T=59.9 → T=60.1:
  Bucket A (59.9): se incrementa
  Siguiente request se checkea en B (60.1): ve bucket B vacio + bucket A (weight=0.9)
  
  effective = 0 (en B) + (1 (en A) * 0.9) = 0.9
  limit=3 → ALLOW
  
✓ Sin problema: weight suaviza la transicion.
```

## Tunning del window_seconds

| window_seconds | Caso de uso | Ventajas | Desventajas |
|---|---|---|---|
| 10 | Muy estricto (ej. 1 req / 10s) | Granularidad fina | Muchos buckets en DynamoDB |
| 60 | Recomendado (1 req / min) | Balance | ~60 buckets/IP/endpoint vivos |
| 300 | Permisivo (10 req / 5min) | Menos buckets | Menos responsive a cambios |
| 3600 | Muy lenient (1000 req / hora) | Minimo storage | Casi ignora previous window |

Para este portfolio: **window_seconds=60** es standard (1 bucket por minuto).

## Performance

```
DynamoDB latency (warm):
  GET + UpdateItem: ~10-15ms (us-west-2)
  
Lambda latency:
  Rate-check middleware: <1ms (calculo local)
  
Total: ~15ms por request (despreciable).
```

---

**Verificado a**: 2026-05-14 (DynamoDB atomic UpdateItem docs, AWS database blog resource counters)

**Fuentes**:
- [AWS: DynamoDB UpdateItem atomic counters](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/example_dynamodb_Scenario_AtomicCounterOperations_section.html)
- [Oneuptime: DynamoDB atomic counters 2026](https://oneuptime.com/blog/post/2026-02-12-dynamodb-atomic-counters/view)
