# common.cache - DynamoDB TTL + SWR + lock distribuido

> Modulo de cache key-value reusable por todas las Lambdas del backend.
> Patron consolidado en `.claude/docs/dynamodb-cache/` (8 docs).

## Quick start

```python
from common.cache import cached, DynamoDBCache

# Decorator (uso recomendado):
@cached(ttl=300, namespace='ssm', tags=['secrets'])
def get_turnstile_secret() -> str:
    return ssm.get_parameter('/portfolio/turnstile-secret')['Value']

# Cliente directo:
cache = DynamoDBCache()
cache.set('key', {'a': 1}, ttl=60, stale_for=120, tags=['analytics'])
value = cache.get('key')                   # {'a': 1} si fresh, None si miss/expired
entry = cache.get_entry('key')             # raw entry para SWR logic
cache.invalidate(tag='analytics')          # bulk soft delete
```

## Estados (CacheStatus)

| Estado | Condicion | Que hace el decorator |
|--------|-----------|----------------------|
| FRESH | now < expires_at | Return cached |
| STALE | expires_at <= now < stale_until | Return cached (sin refresh async; el proximo invocador refresca) |
| EXPIRED | now >= stale_until | Lock + recompute + set + release |
| MISS | item no existe | Lock + compute + set + release |

## Lock distribuido (cache stampede prevention)

Cuando N Lambdas concurrentes pegan a un cache EXPIRED:
1. Cada una intenta `acquire_lock(key)` con ConditionExpression
2. Solo UNA Lambda obtiene el lock; las demas retornan None
3. La que obtuvo el lock recomputa + set + release
4. Las otras hacen busy-wait 500ms + retry get_entry; si encuentran fresh/stale, sirven eso

## Tag-based invalidation

```python
cache.set('secret-A', '...', ttl=300, tags=['secrets', 'ssm'])
cache.set('secret-B', '...', ttl=300, tags=['secrets'])

# Invalida ambos (scan + UpdateItem expires_at=0):
cache.invalidate(tag='secrets')
```

Decision: NO usar GSI por tag (write amplification x2). A escala portfolio
el scan completo cuesta <1 RCU.

## Diferencia con Powertools @idempotent

- `@cached`: NO recomputar valor; ok ejecutar varias veces, devuelve mismo result.
- `@idempotent` (Powertools): NO re-ejecutar handler; protege contra duplicados desde el cliente.

Ver `.claude/docs/dynamodb-cache/07-powertools-idempotency-vs-cache.md`.

## Tabla `portfolio-cache-{stage}` (SPEC-001)

| Atributo | Tipo | Notas |
|----------|------|-------|
| `cache_key` | S (PK) | Format: `{namespace}:{fn}:{hash24}` o `lock:{key}` |
| `value` | S | JSON serializado o base64 (bytes) |
| `encoding` | S | `json` \| `bytes_b64` \| `lock` |
| `expires_at` | N (TTL) | Unix epoch seconds |
| `stale_until` | N | Unix epoch seconds (SWR window) |
| `tags` | L<S> | Lista de tags para invalidacion |
| `metadata` | M | Opcional, no se usa para logica |
