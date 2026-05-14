# 03. Cache Stampede Prevention: Lock distribuido + XFetch

> Problema: cuando un valor cache expira, N Lambdas concurrentes ven cache miss
> y todas recomputan el valor caro al mismo tiempo → **thundering herd problem**.
>
> Solucion: lock distribuido (recomendado) + probabilistic early recomputation (XFetch).

**Verificado**: 2026-05-14 — Pattern validado en articulos theburningmonk, howtech.substack,
system design interviews.

## Problema ilustrado

```
T=0s: Valor "top-countries" cacheado con TTL=300s, no hay lock

T=300s: Valor expira
  Lambda A: cache miss → lock_owner=null → adquiere lock (A es el primero)
  Lambda B: cache miss → lock_owner=A → espera o devuelve stale
  Lambda C: cache miss → lock_owner=A → espera o devuelve stale
  Lambda D: cache miss → lock_owner=A → espera o devuelve stale
  ...
  Lambda N: cache miss → lock_owner=A → espera o devuelve stale

  ✓ Problema RESUELTO: solo A recomputa (N-1 Lambdas evitan recompute)
  ✓ Cost: N request a DynamoDB, 1 recompute, no thundering herd

VS (sin lock):
  Lambda A, B, C, D, N: TODAS recomputan
  → N requests al backend (Neon, SSM, Turnstile)
  → N x costo de recompute
  → Possible timeout de backend si N es grande
```

## Solucion 1: Lock distribuido (RECOMENDADO)

### Mecanica del lock

```python
# Paso 1: Intentar adquirir lock con ConditionExpression
def acquire_lock(cache_key: str, lock_ttl_seconds: int = 5) -> bool:
    """
    Intenta adquirir lock distribuido para evitar cache stampede.
    Returns: True si adquiri el lock, False si alguien ya lo tiene.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['CACHE_TABLE_NAME'])
    
    request_id = os.environ['AWS_REQUEST_ID']  # Lambda request ID unico
    lock_expires = int(time.time()) + lock_ttl_seconds
    
    try:
        # UpdateItem con ConditionExpression: solo si NO hay lock O expired
        table.update_item(
            Key={'cache_key': cache_key},
            UpdateExpression='SET lock_owner = :rid, lock_expires = :exp',
            ConditionExpression=(
                'attribute_not_exists(lock_owner) OR lock_expires < :now'
            ),
            ExpressionAttributeValues={
                ':rid': request_id,
                ':exp': lock_expires,
                ':now': int(time.time()),
            },
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        raise

# Paso 2: Si no adquiri lock, esperar y devolver cached (aunque expirado)
def get_with_lock_wait(cache_key: str, wait_seconds: int = 3) -> dict | None:
    """
    Get con wait si otro Lambda esta recomputando.
    """
    # Intentar adquirir lock
    if acquire_lock(cache_key):
        # Success: yo tengo el lock, debo recompute
        return {'has_lock': True, 'value': None}
    
    # No consegui lock: esperar que otro Lambda termine
    start = time.time()
    while time.time() - start < wait_seconds:
        item = get_item(cache_key)
        if item and item.get('value') and not is_locked(cache_key):
            # Otro Lambda termino y libero el lock, value actualizado
            return {'has_lock': False, 'value': item['value']}
        time.sleep(0.1)  # busy-wait corto (100ms)
    
    # Timeout: devolver ultimo cached (expirado pero mejor que nada)
    item = get_item(cache_key)
    return {
        'has_lock': False,
        'value': item.get('value') if item else None,
    }

# Paso 3: Usar en handler
def handler_turnstile_verify(event, context):
    cache_key = f"turnstile:{hash_token(event['token'])}"
    
    # Intentar get normal
    cached = get_item(cache_key)
    if cached and not is_expired(cached):
        return {'success': True, 'cached': True}
    
    # Cache miss: intentar lock
    lock_result = get_with_lock_wait(cache_key)
    
    if lock_result['has_lock']:
        # Yo tengo el lock → recompute
        result = turnstile_siteverify(event['token'])
        set_item(cache_key, result, ttl=30)
        release_lock(cache_key)
        return {'success': True, 'cached': False, 'recomputed': True}
    elif lock_result['value']:
        # Otro Lambda recomputo, devolver su resultado (stale)
        return {'success': True, 'cached': True, 'stale': True}
    else:
        # Timeout esperando lock, devolver error
        return {'success': False, 'error': 'cache-lock-timeout'}
```

### Ventajas del lock distribuido

✓ **Simple**: solo ConditionExpression en DynamoDB  
✓ **Garantizado**: DynamoDB atomicity  
✓ **Sin infra extra**: mismo DynamoDB que el cache  
✓ **Costo bajo**: 1-2 extra updates per thundering herd  
✓ **TTL built-in**: lock expira automaticamente si Lambda muere  

### Gotchas

⚠ **Lock timeout corto** (ej. 5s): si recompute tarda 10s, otros Lambdas timeout
y devuelven error. Solucion: tuning del timeout segun recompute latency.

⚠ **Busy-wait**: `time.sleep(0.1)` es ineficiente en Lambda. Alternativa:
devolver error si no adquiero lock (cliente reintentar), o usar SWR
para devolver stale sin esperar.

⚠ **Lost update si lock expira**: Lambda A toma lock, recomputa lentamente,
lock expira, Lambda B toma lock, ambas escriben. Mitigation: lock TTL
un poco mayor que max recompute time.

## Solucion 2: Probabilistic early recomputation (XFetch)

### Concepto

En lugar de esperar a que expire exactamente, cada Lambda que accede al cache
decide refrescar probabilísticamente ANTES de la expiracion, con probabilidad
que aumenta exponencialmente hacia el final del TTL.

```python
def should_refresh(created_at: int, ttl_seconds: int, now: int) -> bool:
    """
    XFetch: probabilidad de refresh = 1 - exp(-β * (now - created_at) / ttl)
    donde β es un parametro (ej. 1.0). Esto hace que la probabilidad creza
    exponencialmente hacia el final del TTL.
    
    Interpretacion:
    - Al 50% del TTL: P = 1 - exp(-1.0 * 0.5) = ~39%
    - Al 80% del TTL: P = 1 - exp(-1.0 * 0.8) = ~55%
    - Al 100% del TTL: P = 1 - exp(-1.0 * 1.0) = ~63%
    """
    import math
    import random
    
    age_ratio = (now - created_at) / ttl_seconds
    if age_ratio >= 1.0:
        age_ratio = 0.99  # No dividir por cero
    
    beta = 1.0  # Tuning parameter
    p_refresh = 1 - math.exp(-beta * age_ratio)
    
    return random.random() < p_refresh

def get_with_xfetch(cache_key: str, ttl_seconds: int = 300) -> dict:
    """
    Get con XFetch: si probabilistically decide, refrescar en background.
    """
    item = get_item(cache_key)
    
    if not item:
        # Cache miss: debe refrescar
        return {'value': None, 'needs_refresh': True}
    
    if is_expired(item):
        # Expired: must refresh synchronously
        return {'value': item['value'], 'needs_refresh': True, 'stale': True}
    
    # Cache hit: check si refrescar probabilistically
    created_at = parse_iso_to_epoch(item['created_at'])
    now = int(time.time())
    
    if should_refresh(created_at, ttl_seconds, now):
        # Probability decide: refrescar en background (fire-and-forget)
        # En Lambda, usar asyncio.create_task o threading.Thread (cuidado con execution context)
        trigger_async_refresh(cache_key)
        return {'value': item['value'], 'needs_refresh': False}  # devolver cached
    
    # Probability decide no refrescar
    return {'value': item['value'], 'needs_refresh': False}
```

### Ventajas de XFetch

✓ **Evita thundering herd**: probabilidad distribuida reduce picos de recompute  
✓ **Sin busy-wait**: lambdas devuelven rapido  
✓ **Asimetrica (de-facto)**: primeros request en "expirado" refrescan, ultimos no  
✓ **Matematicamente optimo**: exponential distribution minimiza max load  

### Gotchas

⚠ **Requiere async/threading**: en Lambda, `asyncio.create_task` solo si runtime
asincrono. `threading.Thread` puede no terminar antes de execution context kill.

⚠ **No garantizado**: probabilistica, no deterministica. Puede que 10 Lambdas
decidan refrescar al mismo tiempo (bajo probabilidad).

⚠ **Tuning de beta**: requiere experimentacion. Beta=1.0 es starting point.

## Hybrid: Lock + XFetch (MEJOR)

Combinar ambas:

```python
def get_cached_hybrid(cache_key: str, ttl_seconds: int = 300) -> dict:
    """
    Estrategia hibrida:
    1. Hit + no expired: devolver, probabilistically refresh en background (XFetch)
    2. Miss o expired: intentar lock (distribuido), si no: devolver stale
    """
    item = get_item(cache_key)
    
    if item and not is_expired(item):
        # Fresh: devolver + maybe refresh probabilistically
        if should_refresh(item['created_at'], ttl_seconds):
            trigger_async_refresh(cache_key)
        return {'value': item['value'], 'fresh': True}
    
    # Miss o expired: usar lock distribuido
    if acquire_lock(cache_key):
        # Yo tengo lock: debo recompute
        return {'value': None, 'has_lock': True}
    else:
        # Otro Lambda recomputa: esperar o devolver stale
        lock_result = get_with_lock_wait(cache_key, wait_seconds=2)
        if lock_result['value']:
            return {'value': lock_result['value'], 'stale': True}
        else:
            return {'value': None, 'error': 'cache-lock-timeout'}
```

## Comparacion: Lock vs XFetch vs Hybrid

| Aspecto | Lock distribuido | XFetch | Hybrid |
|--------|------------------|--------|--------|
| Thundering herd prevention | Excelente (100% lock) | Bueno (~65% probabilidad) | Excelente |
| Latencia p99 | Baja (lock-wait <2s) | Baja (sin wait) | Baja |
| Complejidad | Media | Baja | Alta |
| Costo DynamoDB | Medio (+1 update per stampede) | Bajo (+background refresh) | Medio-alto |
| Recomendacion | Valor critico (Turnstile) | Valor no-critico (analytics) | General (balanced) |

## Referencias

- howtech.substack: [Thundering Herd Problem (Cache Stampede): Solutions & Prevention](https://howtech.substack.com/p/thundering-herd-problem-cache-stampede)
- medium: [Cache Stampede & The Thundering Herd Problem](https://medium.com/@sonal.sadafal/cache-stampede-the-thundering-herd-problem-d31d579d93fd)
- bugfree.ai: [Dealing with Cache Stampede and Thundering Herd](https://bugfree.ai/knowledge-hub/dealing-with-cache-stampede-and-thundering-herd)

