# 04. Stale-While-Revalidate (SWR) Pattern

> Patron HTTP popularizado por el header `Cache-Control: max-age=300, stale-while-revalidate=600`.
> Adaptado a DynamoDB: devolver valor expirado rapido mientras se recomputa en background.
>
> Ideal para queries caras (Neon, GeoIP) que toleran staleness (30min OK).

**Verificado**: 2026-05-14 — Pattern de AWS, CloudFront, y SWR React lib.

## Concepto

```
T=0s: Query Neon computa top-countries, guardar con TTL=300s, SWR window=600s

T=300s: valor expira (exits max-age)
  Client A: GET top-countries → devolver valor (aunque expired), fire-and-forget refresh
  Client B: GET top-countries → devolver mismo valor (aunque expired)
  Background: una Lambda refrescando (async)

T=305s: Background Lambda termina, actualiza valor
  Client C: GET top-countries → devolver valor NUEVO (no expirado)

T=600s: SWR window cierra
  Proxima expired: DEBE recompute sincrono

Ventajas:
  ✓ Clientes nunca espera recompute (latencia baja)
  ✓ Cache hit rate maxima (devolvemos aunque expired)
  ✓ Backend nunca ve spike (refresco asincronico)
  ✓ Graceful degradation: si error refrescar, devolver stale (mejor que error)
```

## Estados de cache

```python
from enum import Enum
from datetime import datetime, UTC

class CacheStatus(Enum):
    FRESH = "fresh"           # now < expires_at
    STALE = "stale"           # expires_at <= now < stale_until
    EXPIRED = "expired"       # now >= stale_until
    MISSING = "missing"       # no existe en cache

def get_cache_status(item: dict | None, now: int | None = None) -> CacheStatus:
    """Determinar el estado del cache."""
    now = now or int(time.time())
    
    if not item:
        return CacheStatus.MISSING
    
    expires_at = item.get('expires_at')
    stale_until = item.get('stale_until')
    
    if now < expires_at:
        return CacheStatus.FRESH
    elif stale_until and now < stale_until:
        return CacheStatus.STALE
    else:
        return CacheStatus.EXPIRED
```

## Implementacion

### 1. Set con SWR metadata

```python
def set_with_swr(
    cache_key: str,
    value: dict,
    ttl_seconds: int = 300,
    swr_seconds: int = 300,  # SWR window
) -> None:
    """
    Guardar valor cacheado con SWR window.
    
    Ejemplo:
        set_with_swr(
            'query:top-countries',
            {'countries': [...]},
            ttl_seconds=300,      # max-age
            swr_seconds=300,      # stale-while-revalidate
        )
    
    Resultado en DynamoDB:
        expires_at = now + 300 (5 min)
        stale_until = now + 600 (10 min, SWR window)
    """
    import json
    from datetime import datetime, UTC
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['CACHE_TABLE_NAME'])
    
    now = int(time.time())
    
    table.put_item(
        Item={
            'cache_key': cache_key,
            'value': json.dumps(value),
            'value_type': 'json',
            'created_at': datetime.now(UTC).isoformat(),
            'expires_at': now + ttl_seconds,          # max-age
            'stale_until': now + ttl_seconds + swr_seconds,  # SWR extension
            'tags': ['analytics', 'neon'],  # opcional, para invalidation
        }
    )
```

### 2. Get con SWR (devolver stale + async refresh)

```python
def get_with_swr(
    cache_key: str,
    recompute_fn: Callable,
    ttl_seconds: int = 300,
    swr_seconds: int = 300,
) -> dict | None:
    """
    Get con SWR: devolver stale mientras se refresca en background.
    
    Args:
        cache_key: clave del cache
        recompute_fn: funcion que computa valor (ej. query Neon)
        ttl_seconds: max-age (valor fresco)
        swr_seconds: stale-while-revalidate window
    
    Returns:
        valor (fresco, stale, o None si error critico)
    
    Behavior:
        FRESH: devolver
        STALE: devolver + async refresh
        EXPIRED: sync refresh (devolver cuando listo)
        MISSING: sync refresh
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['CACHE_TABLE_NAME'])
    
    # Get del cache
    response = table.get_item(Key={'cache_key': cache_key})
    item = response.get('Item')
    
    status = get_cache_status(item)
    
    if status == CacheStatus.FRESH:
        # Devolver rapido
        return json.loads(item['value'])
    
    elif status == CacheStatus.STALE:
        # Devolver stale + async refresh
        trigger_async_refresh(cache_key, recompute_fn, ttl_seconds, swr_seconds)
        return json.loads(item['value'])
    
    elif status == CacheStatus.EXPIRED or status == CacheStatus.MISSING:
        # Expired o missing: recompute sincrono
        try:
            value = recompute_fn()
            set_with_swr(cache_key, value, ttl_seconds, swr_seconds)
            return value
        except Exception as e:
            # Si error: intentar devolver stale (graceful degradation)
            if item:
                return json.loads(item['value'])
            else:
                raise  # No hay stale fallback, propagar error

def trigger_async_refresh(
    cache_key: str,
    recompute_fn: Callable,
    ttl_seconds: int,
    swr_seconds: int,
) -> None:
    """
    Disparar refresh asincrono en background.
    
    CUIDADO: En Lambda, asyncio.create_task y threading.Thread pueden no
    terminar antes de que se mate el execution context. Recomendacion:
    invocar Lambda separada via SQS/SNS, o usar asyncio + esperar.
    """
    import asyncio
    
    # Opcion 1: asyncio (solo si handler es async)
    try:
        # Asumir que esta en contexto asincrono
        asyncio.create_task(run_refresh_async(cache_key, recompute_fn, ttl_seconds, swr_seconds))
    except RuntimeError:
        # No contexto asincrono: hacer sync (mejor que no hacer nada)
        try:
            value = recompute_fn()
            set_with_swr(cache_key, value, ttl_seconds, swr_seconds)
        except Exception:
            pass  # Best effort, no propagar error de refresh

async def run_refresh_async(cache_key, recompute_fn, ttl_seconds, swr_seconds):
    """Refresh asincrono."""
    try:
        value = await recompute_fn()  # Asumir que recompute_fn es async
        set_with_swr(cache_key, value, ttl_seconds, swr_seconds)
    except Exception as e:
        print(f"Background refresh failed for {cache_key}: {e}")
        # No propagar, es best-effort
```

### 3. Ejemplo: Query Neon con SWR

```python
import asyncio
from typing import Any

async def handler_analytics(event, context):
    """
    Lambda que devuelve top-countries.
    - Cacheada por 5 minutos (FRESH)
    - SWR window de 10 minutos (devolver STALE mientras se refresca)
    - Si EXPIRED: bloquea hasta recompute
    """
    cache_key = "query:top-countries"
    
    async def query_neon() -> dict[str, Any]:
        """Query cara a Neon (5s típico)."""
        # conn = await neon_pool.acquire()
        # result = await conn.fetchrow("SELECT country, COUNT(*) as count FROM events GROUP BY country ORDER BY count DESC LIMIT 10")
        # await neon_pool.release(conn)
        # return [dict(row) for row in result]
        
        # Simulado:
        await asyncio.sleep(1)  # 1s simulado
        return {
            "countries": [
                {"country": "US", "count": 1523},
                {"country": "MX", "count": 823},
                {"country": "CL", "count": 423},
            ]
        }
    
    # Get con SWR
    value = get_with_swr(
        cache_key,
        query_neon,
        ttl_seconds=300,       # 5 minutos fresh
        swr_seconds=300,       # 5 minutos stale-while-revalidate
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(value),
        'headers': {
            'Cache-Control': 'max-age=300, stale-while-revalidate=300',
        }
    }
```

## Configuracion por use case

| Use case | TTL (max-age) | SWR window | Razon |
|----------|---------------|-----------|-------|
| SSM Parameter Store | 5min | 0 (no SWR) | Secrets, no debe ser stale |
| Turnstile siteverify | 30s | 0 (no SWR) | Token single-use, staleness invalida |
| Neon query (analytics) | 30min | 30min | Datos historicos, tolera 1h de staleness |
| GeoIP lookup | 24h | 7d | Datos casi-estaticos |
| Config del proyecto | 1h | 1d | Cambios raros, tolera lag |

## Estados finales

La tabla `cache` tendr items como:

```yaml
# FRESH: normal, devolver rapido
cache_key: "query:top-countries"
expires_at: 1747334400
stale_until: 1747335000
# now < expires_at → FRESH

# STALE: devolver rapido + async refresh
cache_key: "query:top-countries"
expires_at: 1747334380   # Pasado
stale_until: 1747335000
# expires_at <= now < stale_until → STALE

# EXPIRED: debe recompute sincrono
cache_key: "query:top-countries"
expires_at: 1747334300   # Muy pasado
stale_until: 1747335000  # Pasado
# now >= stale_until → EXPIRED
```

## Ventajas de SWR

✓ **Baja latencia**: clientes nunca esperan recompute  
✓ **Alta disponibilidad**: si backend falla, devolver stale (graceful degradation)  
✓ **Bajo costo backend**: refresco asincronico, no spike de requests  
✓ **Cache hit rate**: 100% mientras stale_until activo  
✓ **Simple**: no necesita locks distribuidos  

## Gotchas

⚠ **Async en Lambda**: `asyncio.create_task` puede no terminar antes de execution
context kill. Solucion: invocar Lambda separada (via SNS/SQS) o esperar el task.

⚠ **TTL eventual**: DynamoDB borra items cuando `expires_at` es pasado, pero puede
tardar 48h. Mientras tanto, item ocupa storage. Acceptable si staleness es OK.

⚠ **Diferencia con CloudFront SWR**: CloudFront `stale-while-revalidate` es header
HTTP que el navegador/CDN entiende. DynamoDB SWR es aplicacion-level (nosotros
manejamos los estados).

## Referencias

- AWS: [CloudFront stale-while-revalidate support](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-cloudfront-stale-while-revalidate-stale-if-error-cache-control-directives/)
- theburningmonk.com: [All you need to know about caching for serverless applications](https://theburningmonk.com/2019/10/all-you-need-to-know-about-caching-for-serverless-applications/)
- HTTP RFC 7234: [Cache-Control Extensions](https://datatracker.ietf.org/doc/html/rfc7234)

