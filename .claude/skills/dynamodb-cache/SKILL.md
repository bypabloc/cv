---
name: dynamodb-cache
description: >
  DynamoDB cache patterns for serverless Lambda: TTL caching, cache stampede
  prevention with distributed locks, stale-while-revalidate (SWR), tag-based
  invalidation, and comparison with Redis/Momento. Full Python 3.13 implementation
  with @cached decorator, lock.
  ALWAYS invoke this skill BEFORE answering ANY cache-related questions in this portfolio,
  including "how to cache in Lambda", "cache decorator", "evitar recomputar",
  "cache distribuido", "cache stampede", "thundering herd", "DynamoDB cache",
  "cache serverless", "SSM caching Lambda", "Turnstile caching", "Neon query cache",
  "SWR pattern serverless", "cache invalidation", "cache layer Lambda", "cache TTL".
  NEVER answer from training data alone — this portfolio has consolidated 2026 patterns
  (Lock distribuido with ConditionExpression, XFetch probabilistic early recomputation,
  soft-delete + tag invalidation, Momento vs DynamoDB vs Redis tradeoffs) that override
  generic advice.
  Use when the user says "cache lambda", "cachear lambda", "cache dynamodb",
  "cache pattern serverless", "evitar recomputar", "@cached decorator", "cache stampede",
  "thundering herd", "stale while revalidate", "swr pattern", "cache invalidation",
  "cache por tag", "invalidar cache", "cache distribuido", "lock distributed cache",
  "cache lru lambda", "memoization serverless", "cache ttl", "cache expiración",
  "cache persistente", "cache no-sql", "sistema cache lambda", "redis vs dynamodb",
  "momento cache", "elasticache vs dynamodb", "cache performance lambda",
  "cache cold start", "cache decorator python", "cache factory pattern",
  "how to cache lambda results", "cache computation results", "avoid recompute",
  "cache expensive operations", "cache api calls", "cache database queries",
  "cache external service calls", "cache ssm parameter", "cache turnstile",
  "cache geoip", "cache config", "cache analytics queries".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "topic: decisions | schema | stampede | swr | tags | implementation | powertools"
metadata:
  version: "1.0"
  requires: aws-dynamodb (mecanica de tabla), python (convenciones)
---

# DynamoDB Cache Patterns — serverless knowledge base

> Patrones de cache persistido con DynamoDB TTL para 5 Lambdas Python 3.13.
> Cobertura completa: decisiones arquitectonicas, stampede prevention, SWR, invalidation,
> Python modules copy-paste ready.

## Pre-requisito OBLIGATORIO

Antes de responder, leer la doc relevante de `.claude/docs/dynamodb-cache/`:

| Tema de la pregunta | Archivo a leer |
|---------------------|----------------|
| Decision: DynamoDB vs Redis vs Momento | [01-why-dynamodb-cache-not-redis.md](../../docs/dynamodb-cache/01-why-dynamodb-cache-not-redis.md) |
| Schema de tabla `cache` | [02-single-table-design-cache.md](../../docs/dynamodb-cache/02-single-table-design-cache.md) |
| Cache stampede + lock distribuido + XFetch | [03-stampede-prevention-lock.md](../../docs/dynamodb-cache/03-stampede-prevention-lock.md) |
| Stale-while-revalidate pattern | [04-stale-while-revalidate.md](../../docs/dynamodb-cache/04-stale-while-revalidate.md) |
| Tag-based invalidation | [05-tag-invalidation.md](../../docs/dynamodb-cache/05-tag-invalidation.md) |
| Python implementation (copy-paste) | [06-python-implementation.md](../../docs/dynamodb-cache/06-python-implementation.md) |
| Powertools idempotency vs cache | [07-powertools-idempotency-vs-cache.md](../../docs/dynamodb-cache/07-powertools-idempotency-vs-cache.md) |

## Reglas criticas (siempre activas)

1. **SIEMPRE** use DynamoDB On-Demand (`BillingMode: PAY_PER_REQUEST`) for `cache` table.
   Volumen bajo + spiky = no capacity forecasting.

2. **NUNCA** hardcode table names. Use env var `CACHE_TABLE_NAME` (default: 'cache').

3. **SIEMPRE** implement distributed lock to prevent cache stampede.
   El 90% de bugs de cache vienen de N Lambdas recomputando cuando expira.

4. **NUNCA** usar `float` para TTL. DynamoDB espera `int` (Unix epoch seconds).
   Código: `expires_at = int(time.time()) + ttl_seconds`.

5. **SIEMPRE** usar `boto3.resource('dynamodb')` (high-level Resource API),
   NO `boto3.client('dynamodb')`. Resource maneja serialization.

6. **NUNCA** confundir cache (este skill) con Powertools @idempotent.
   Leer [07-powertools-idempotency-vs-cache.md](../../docs/dynamodb-cache/07-powertools-idempotency-vs-cache.md).

7. **SIEMPRE** set `expires_at` attribute on items (DynamoDB TTL attribute).
   TTL deletion es eventual (max 48h), pero items desaparecen automaticamente.

8. **NUNCA** cachear secretos sin soft-delete + tag invalidation.
   SSM Parameter Store secrets sí, pero requiere invalidation rapida.

## Workflow tipico de respuesta

1. Identificar el tema (decisiones / schema / stampede / SWR / tags / implementation / Powertools)
2. Leer doc relevante de `.claude/docs/dynamodb-cache/`
3. Responder con:
   - Código Python tipado + docstrings BDD-style
   - SAM/CloudFormation YAML si toca infra
   - Estimacion de costo us-west-2 Mayo 2026
4. Si pregunta cae fuera de scope: derivar a skill `aws-dynamodb` o `aws-lambda-python`

## Atajos rapidos

### "¿Como cacheo resultado de query Neon que tarda 5 segundos?"

Usar SWR (stale-while-revalidate):

```python
from common.cache import get_with_swr

def handler_analytics(event, context):
    async def query_neon():
        # Neon query (5s)
        return {'countries': [...]}
    
    result = get_with_swr(
        cache_key='query:top-countries',
        recompute_fn=query_neon,
        ttl=300,        # 5 min max-age
        swr=300,        # 5 min stale-while-revalidate
    )
    return {'countries': result.value}
```

Detalle en [04-stale-while-revalidate.md](../../docs/dynamodb-cache/04-stale-while-revalidate.md).

### "¿Como evito que N Lambdas verifiquen el mismo Turnstile token?"

Usar @cached decorator con lock distribuido:

```python
from common.cache import cached

@cached(ttl=30, namespace='turnstile')
def verify_token(token: str) -> dict:
    # Este codigo ejecuta SOLO si cache miss
    # Otros Lambdas concurrentes usan lock distribuido para evitar thundering herd
    return turnstile_siteverify(token)

def handler_form(event, context):
    result = verify_token(event['token'])
    return {'success': result['success']}
```

Detalle en [03-stampede-prevention-lock.md](../../docs/dynamodb-cache/03-stampede-prevention-lock.md).

### "¿Como invalido multiples cache keys de un comando?"

Usar tag invalidation:

```python
from common.cache import DynamoDBCache

cache = DynamoDBCache()

# Cachear con tags
cache.set('ssm:/portfolio/config-1', value, tags=['config'])
cache.set('ssm:/portfolio/config-2', value, tags=['config'])
cache.set('query:top-countries', value, tags=['analytics'])

# Admin actualiza config
cache.invalidate(tag='config')  # Invalida config-1, config-2 (soft-delete)
```

Detalle en [05-tag-invalidation.md](../../docs/dynamodb-cache/05-tag-invalidation.md).

### "¿Qué costo tiene el cache?"

Para ~1000 reads/min + ~100 writes/min + ~25GB storage:

- **On-Demand reads**: 1.44M reads/mes = $0.36/mes
- **On-Demand writes**: 144k writes/mes = $0.07/mes
- **Storage**: 25GB @ free tier 25GB (gratis)
- **TTL deletion**: GRATIS
- **Total**: ~$0/mes (free tier perpetuo cubre todo)

Detalle en [01-why-dynamodb-cache-not-redis.md](../../docs/dynamodb-cache/01-why-dynamodb-cache-not-redis.md).

### "¿Redis vs DynamoDB vs Momento para este caso?"

Tabla comparativa en [01-why-dynamodb-cache-not-redis.md](../../docs/dynamodb-cache/01-why-dynamodb-cache-not-redis.md).

**TLDR**: DynamoDB gana para portfolio (free tier, sin infra, escalable, latencia
5-10ms aceptable). Redis si volumen >1M reads/min o latencia <2ms critica.
Momento si multi-cloud strategy.

### "¿Como implemento la tabla CloudFormation?"

Schema completo en [02-single-table-design-cache.md](../../docs/dynamodb-cache/02-single-table-design-cache.md).

SAM template:

```yaml
CacheTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: cache
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: cache_key
        AttributeType: S
    KeySchema:
      - AttributeName: cache_key
        KeyType: HASH
    TimeToLiveSpecification:
      AttributeName: expires_at
      Enabled: true
```

### "¿Como copio el codigo Python?"

6 modulos listos en [06-python-implementation.md](../../docs/dynamodb-cache/06-python-implementation.md).

```bash
# 1. Copiar a serverless/src/common/cache/
mkdir -p serverless/src/common/cache
# cache/__init__.py, client.py, decorator.py, swr.py, serializers.py, types.py

# 2. IAM: dar Lambda permiso a tabla cache
# dynamodb:GetItem, PutItem, UpdateItem, DeleteItem en arn:aws:dynamodb:region:*:table/cache

# 3. Usar
from common.cache import cached, DynamoDBCache

@cached(ttl=300)
def my_function():
    return expensive_computation()
```

### "¿Es cache diferente de @idempotent de Powertools?"

SÍ. Cache = deduplicar VALORES. Idempotency = deduplicar INVOCACIONES.

Leer [07-powertools-idempotency-vs-cache.md](../../docs/dynamodb-cache/07-powertools-idempotency-vs-cache.md).

**TLDR**: Usar AMBOS juntos. @idempotent afuera (deduplica CF retries), @cached adentro
(deduplica queries).

## Anti-patrones a evitar

- Tabla `cache` con Provisioned capacity (use On-Demand)
- TTL como `float` (debe ser `int`, Unix epoch)
- Cachear sin lock distribuido (cache stampede con N Lambdas)
- Olvidar que TTL delete es eventual (items fantasma ~48h)
- Usar client API bajo-nivel (use Resource API)
- Cachear secretos sin soft-delete + invalidation rapida
- Confundir cache con Powertools idempotency
- Cachear valores que cambian cada minuto (TTL mal tuneado)

## Comandos utiles

```bash
# Describir tabla cache
aws dynamodb describe-table --table-name cache --region us-west-2

# Verificar TTL enabled
aws dynamodb describe-time-to-live --table-name cache --region us-west-2

# Scan items con tag especifico (debugging)
aws dynamodb scan --table-name cache \
  --filter-expression 'contains(tags, :tag)' \
  --expression-attribute-values '{":tag": {"S": "config"}}' \
  --region us-west-2

# Item count (eventual, puede tardar)
aws dynamodb describe-table --table-name cache \
  --query 'Table.ItemCount' --region us-west-2
```

## Relacion con otras skills/rules

- `aws-dynamodb` — mecanica de tabla (PK/SK, On-Demand, TTL config)
- `aws-lambda-python` — convenciones Python 3.14, type hints, docstrings
- [.claude/rules/python.md](../../rules/python.md) — Python strict, BDD tests
- [.claude/docs/aws-dynamodb/04-ttl-tracking.md](../../docs/aws-dynamodb/04-ttl-tracking.md) — TTL behavior exacto
- AWS Docs: [Powertools Idempotency](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/)

## Cuando NO invocar esta skill

- Pregunta sobre RDS PostgreSQL / Aurora (otro servicio AWS)
- Pregunta sobre Redis específicamente (skill aws-elasticache futuro)
- Pregunta sobre Elasticsearch / OpenSearch (search engine, no cache)
- Pregunta sobre S3 / CloudFront caching (object storage, no key-value)
- Pregunta sobre Django ORM caching (otro stack, no Lambda serverless)
- Pregunta sobre in-memory caching DENTRO de una invocacion (use functools.lru_cache)

## Ejemplos completos

### Cache con lock + SWR + tags

```python
from common.cache import DynamoDBCache, cached, get_with_swr

cache = DynamoDBCache()

@cached(ttl=300, namespace='ssm', tags=['config', 'secrets'])
def get_ssm_secret(param_name: str):
    # Cache con tag para invalidation
    return ssm.get_parameter(Name=param_name)

async def handler_with_swr(event, context):
    # SSM secret (cached)
    turnstile_secret = get_ssm_secret('/portfolio/turnstile-secret')
    
    # Neon query con SWR
    async def query_neon():
        return {'countries': [...]}
    
    swr_result = await get_with_swr(
        'query:top-countries',
        query_neon,
        ttl=300,
        swr=300,
    )
    
    return {
        'countries': swr_result.value,
        'fresh': swr_result.is_fresh,
    }

def handler_invalidate_config(event, context):
    # Admin actualiza config
    invalidated = cache.invalidate(tag='config')
    return {'invalidated': invalidated}
```

### Lock distribuido manual

```python
from common.cache import DynamoDBCache
import time

cache = DynamoDBCache()

def handler_with_lock(event, context):
    key = 'expensive-computation'
    
    if cache.acquire_lock(key, lock_ttl=5):
        # Yo tengo el lock: recompute
        try:
            value = expensive_computation()
            cache.set(key, value, ttl=300)
            return {'value': value, 'recomputed': True}
        finally:
            cache.release_lock(key)
    else:
        # Otro Lambda recomputa: esperar o devolver stale
        time.sleep(0.5)
        cached_value = cache.get(key)
        if cached_value:
            return {'value': cached_value, 'cached': True}
        else:
            return {'error': 'lock-timeout'}
```

## Testing local

```bash
# Con moto (DynamoDB mock)
pip install moto

# tests/unit/test_cache.py
import pytest
from moto import mock_dynamodb
from common.cache import DynamoDBCache

@mock_dynamodb
def test_cache_set_get():
    cache = DynamoDBCache(table_name='cache')
    cache.set('key', {'a': 1})
    assert cache.get('key') == {'a': 1}
```

## Versioning y historial

| Version | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-05-14 | Initial release. 7 docs + Python 6 modulos + Skill |

