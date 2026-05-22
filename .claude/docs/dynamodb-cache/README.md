# DynamoDB Cache Patterns Knowledge Base

> Patrones de cache persistido con DynamoDB TTL para serverless Lambda (Python 3.13).
> Cubre single-table design, cache stampede prevention, stale-while-revalidate, invalidación por tag,
> y comparación con alternativas (Redis, Momento, ElastiCache).
> Todos los patrones documentados y verificados para 2026.

**Verificado**: 2026-05-14 — Contenido alineado con AWS Powertools Idempotency 2.44.0, DynamoDB TTL
behavior (48h eventual delete), Momento 2026 pricing.

## Cuando leer cada archivo

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Decision: DynamoDB vs Redis vs Momento vs in-memory | [01-why-dynamodb-cache-not-redis.md](./01-why-dynamodb-cache-not-redis.md) | Entender el tradeoff arquitectonico de este proyecto |
| Schema de tabla `cache` (single-table) | [02-single-table-design-cache.md](./02-single-table-design-cache.md) | Antes de crear la tabla CloudFormation |
| Cache stampede problem + lock distribuido + XFetch | [03-stampede-prevention-lock.md](./03-stampede-prevention-lock.md) | Implementar `@cached` decorator sin thundering herd |
| Stale-while-revalidate pattern (SWR) | [04-stale-while-revalidate.md](./04-stale-while-revalidate.md) | Para queries Neon que toleran staleness |
| Tag-based invalidation + soft delete | [05-tag-invalidation.md](./05-tag-invalidation.md) | Cachear con categoria + invalidar por dominio |
| Python implementation COMPLETA (copy-paste ready) | [06-python-implementation.md](./06-python-implementation.md) | Copiar modulos a `serverless/lambda/shared/cache/` |
| AWS Powertools Idempotency vs este cache | [07-powertools-idempotency-vs-cache.md](./07-powertools-idempotency-vs-cache.md) | Usar ambos juntos en handlers criticos |

## Reglas criticas

1. **SIEMPRE** usar DynamoDB On-Demand (`BillingMode: PAY_PER_REQUEST`) para tabla `cache`.
   Volumen bajo + spiky = no forecasting de capacity.

2. **NUNCA** hardcodear tabla names. Usar `os.environ['CACHE_TABLE_NAME']` inyectado
   por Lambda `Environment.Variables`.

3. **SIEMPRE** implementar lock distribuido para evitar cache stampede.
   El 90% de los bugs de cache vienen de que N Lambdas recomputan el mismo valor
   cuando expira (thundering herd).

4. **NUNCA** usar `float` para TTL. DynamoDB espera `int` (Unix epoch seconds).
   Codigo: `expires_at = int(time.time()) + ttl_seconds`.

5. **SIEMPRE** usar `boto3.resource('dynamodb')` (high-level Resource API),
   NO `boto3.client('dynamodb')`. Resource maneja serialization automaticamente.

6. **NUNCA** olvidar que TTL deletion es eventual (max 48h). No es atomico.
   Para datos sensibles (tokens), usar soft-delete + explicito `delete_item()`.

7. **SIEMPRE** poner `expires_at` como atributo del item, NO como column separada.
   DynamoDB TTL lee un solo atributo global por tabla.

8. **NUNCA** confundir cache de valores (este proyecto) con idempotency de handlers
   (AWS Powertools). Leer [07-powertools-idempotency-vs-cache.md](./07-powertools-idempotency-vs-cache.md).

## Navegacion rapida

- **Empezar aqui**: Lee 01 (decision arquitectonica) + 02 (schema)
- **Implementar cache basico**: Lee 06 (Python), copia a `serverless/lambda/shared/cache/`
- **Problema: multiples Lambdas lanzan el mismo recompute**: Lee 03 (lock distribuido)
- **Problema: query cara que puede esperar 30min**: Lee 04 (SWR)
- **Problema: invalidar multiples keys con un comando**: Lee 05 (tag invalidation)
- **Comparacion tecnica**: Lee 01 (DynamoDB vs alternativas)

## Quick start: copiar el codigo

```bash
# 1. Leer 06-python-implementation.md
# 2. Crear dir
mkdir -p serverless/lambda/shared/cache

# 3. Copiar los 5 modulos
# cache/__init__.py, cache/client.py, cache/decorator.py, cache/swr.py, cache/serializers.py

# 4. Usar en handler
from common.cache import cached

@cached(ttl=300, namespace='queries')
def get_top_countries():
    # query Neon
    return results
```

## Estimacion de costo (2026, us-east-1)

Para ~1000 cache reads/min + ~100 writes/min + ~25GB storage:

- **On-Demand reads**: 1.44M reads/mes = $0.36/mes
- **On-Demand writes**: 144k writes/mes = $0.07/mes
- **Storage**: 25GB @ $0.25/GB-mo = $6.25/mes (dentro del free tier 25GB)
- **TTL deletion**: GRATIS (no consume WCU)
- **Total**: ~$0 (free tier perpetuo cubre todo)

Si se excede free tier: $0.25/M reads, $1.25/M writes, $0.25/GB-mo storage.

## Anti-patrones

- ❌ Tabla `cache` con Provisioned capacity en lugar de On-Demand
- ❌ TTL como `float` en lugar de `int` (Unix epoch)
- ❌ Cachear sin lock → cache stampede con N Lambdas recomputando
- ❌ Olvidar que TTL delete es eventual (max 48h) → items fantasma
- ❌ Usar client API bajo-nivel en lugar de Resource API
- ❌ GSI en tabla `cache` sin necesidad (doble write cost)
- ❌ Cachear valores sensibles (tokens, secrets) sin soft-delete
- ❌ Confundir cache (este proyecto) con Powertools idempotency

## Relacion con otras skills/docs

- [.claude/skills/aws-dynamodb/SKILL.md](../../skills/aws-dynamodb/SKILL.md) — mecanica de DynamoDB (PK/SK, On-Demand, TTL config)
- [.claude/docs/aws-dynamodb/04-ttl-tracking.md](../aws-dynamodb/04-ttl-tracking.md) — comportamiento exacto de TTL en DynamoDB
- [.claude/rules/python.md](../../rules/python.md) — convenciones Python 3.14, type hints obligatorios
- AWS Docs: [Powertools Idempotency](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/)
- AWS Docs: [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/time-to-live-ttl-before-you-start.html)

## Versioning

| Version | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-05-14 | Initial release. Patrones de cache, stampede prevention, SWR, tag invalidation. |

