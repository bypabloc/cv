# 01. Decision: DynamoDB vs Redis vs Momento vs In-Memory

> Analisis comparativo: por que este portfolio usa DynamoDB TTL como cache layer
> en lugar de Redis, ElastiCache, Momento, o in-memory dict.

**Verificado**: 2026-05-14 — Precios confirmados con Momento pricing, AWS DynamoDB free tier perpetuo.

## Contexto del proyecto

- 5 Lambdas Python 3.13 arm64 en us-west-2
- Volumen: ~1000 cache reads/min (picos), ~100 writes/min
- Use cases: SSM Parameter Store secrets, Turnstile siteverify, queries Neon,
  GeoIP lookups, config del proyecto
- Cold start latency critica para portfolio
- Budget: free tier preferido, <$0.50/mes aceptable

## Opciones evaluadas

| Opcion | Pros | Cons | Mejor para |
|--------|------|------|-----------|
| **DynamoDB TTL** | ✓ Free tier perpetuo (25GB) ✓ No infra ✓ Escala automatica ✓ TTL deletion sin costo ✓ Cold start <500ms ✓ Integracion nativa boto3 | ✗ Latencia 5-10ms (vs <1ms Redis) ✗ No Pub/Sub ✗ TTL delete eventual (48h) ✗ No LRU eviction nativo ✗ Eventual consistency | Este proyecto: serverless, baja latencia aceptable, volumen bajo, zero infra |
| **Redis (ElastiCache)** | ✓ <1ms latency ✓ Pub/Sub para invalidation ✓ LRU eviction nativo ✓ TTL exacto ✓ Herramientas maduras (Redlock, etc) | ✗ $14-30+/mes minimo ✗ VPC requirement = 10-15s cold start ✗ No scale-to-zero ✗ Overengineering para volumen bajo | Microservicios con baja latencia critica, volumen alto |
| **Momento Serverless Cache** | ✓ <10ms latency ✓ Scale-to-zero ✓ Free tier 50GB/mes (2026) ✓ No VPC ✓ HTTP JSON API | ✗ Vendor lock-in ✗ Pricing opacity (usage-based) ✗ Menos maduro que Redis ✗ Latencia aun peor que DynamoDB en 2026 | Startups en AWS, baja latencia pero no critica |
| **In-memory dict** | ✓ 0ms latencia ✓ Gratis ✓ Cero dependencias | ✗ Perdido en cold start ✗ No cross-Lambda sharing ✗ No TTL real ✗ Inutil para cache persistente | Cache temporal dentro de una invocacion (micro-cache) |

## Analisis detallado por opcion

### DynamoDB TTL (GANADOR)

**Por que ganador**:
- Free tier perpetuo (25GB + 2.5M reads + 1M writes/mes) cubre 100x del volumen proyectado
- Sin infra: DynamoDB es "serverless" en AWS
- Escala automatica: no hay forecasting de capacity
- Integracion nativa con Lambda via boto3 Resource API
- TTL deletion es GRATIS (no consume WCU)
- Cold start: <500ms (socket SSL a DynamoDB regional)

**Latencia**: 5-10ms promedio (red roundtrip us-west-2).
- Aceptable para: config, SSM Parameter Store caching, queries Neon (tolera 30min staleness)
- Inaceptable para: real-time game leaderboards, financial ticks

**Problemas resueltos**:
1. **Cache stampede**: lock distribuido via `UpdateItem` con `ConditionExpression` (doc 03)
2. **TTL eventual**: soft-delete + tag invalidation para datos sensibles (doc 05)
3. **No Pub/Sub**: tag-based invalidation via Scan (doc 05)

**Gotcha 2026**: AWS cambio en Nov 2024 a "free tier perpetuo" para On-Demand mode.
Verifica billing console: si ves "DynamoDB free tier" bajo usage, esta activo.

### Redis / ElastiCache

**Cost breakdown** (2026):
- `cache.t4g.micro`: $0.012/hora = $8.64/mes (smallest, arm64)
- `cache.t4g.small`: $0.025/hora = $18/mes
- VPC NAT Gateway: $0.45/hora (when accessed from outside VPC) = $324/mes (saltar si mismo VPC)
- Total minimo: $18-20/mes sin NAT, $340+/mes con NAT

**Cold start impact**: VPC requirement agrega 10-15s a cold start (ENI attachment).
Para portfolio con focus en SEO + LCP, esto es killer.

**Cuando elegir Redis**:
- Volumen >1M reads/min (DynamoDB on-demand se pone caro)
- Latencia <2ms critica (real-time features)
- Pub/Sub pattern necesario (broadcast invalidation)
- LRU eviction automatico requerido (datos de size variable)
- Microcaching de resultados de queries complejas (mecanismo nativo)

### Momento Serverless Cache

**Pricing (2026)**:
- Free tier: 50GB/mes + 5000 API requests/mes
- Paid: $0.50/GB beyond free tier

**Gotcha**: "requests/mes" en Momento es por operacion (get/set/delete).
1000 reads/min = 1.44M requests/mes = **fuera del free tier**.
Costo estimado: $0.50/mo (mínimo billing tier).

**Ventajas vs DynamoDB**:
- Latencia 5-10ms (similar DynamoDB, pero con mas predicibilidad)
- HTTP API mas simple que boto3 (JSON REST)
- Vendor abstraction mejor que DynamoDB (portable a otra plataforma)

**Problemas**:
- Vendor lock-in a Momento (vs DynamoDB que es AWS standard)
- Pricing opacity: "usage-based" sin detalles publicos en 2026
- Menos maduro: menos examples, menos StackOverflow support
- Eventual consistency como DynamoDB (no es advantage)

**Cuando elegir Momento**:
- Multi-cloud strategy (Momento es agnóstico a cloud)
- Evitar dependencia de AWS
- Team ya familiar con Momento (improbable para portfolio)

### In-Memory Dict (module scope)

```python
_cache = {}  # cache temporal

def get_cached(key, ttl=300):
    if key in _cache:
        value, expires = _cache[key]
        if time.time() < expires:
            return value
    return None
```

**Pros**: 0ms latencia, cero dependencias.

**Cons**: Muere en cold start (Lambda container nuevo = nuevo Python process = dict vacio).
Util solo para micro-cache dentro de una invocacion (ej. evitar parsear JSON 3 veces).

**Cuando elegir in-memory**: Nunca como primary cache. Solo como L1 dentro de handler
para evitar deserializacion repetida en bucles.

## Conclusion: DynamoDB TTL es la opcion correcta para este portfolio

| Criterio | Score (0-10) |
|----------|------------|
| Costo | 10 (gratis con free tier) |
| Latencia aceptable | 7 (5-10ms, OK para use cases) |
| Cold start | 10 (sin VPC, <500ms) |
| Maduracion / ecosystem | 9 (AWS standard, well-documented) |
| Escala | 10 (automatica, on-demand) |
| Simplicidad | 8 (boto3 Resource API + TTL config) |
| **Total** | **9.0/10** |

## Hybrid approach (futuro escalamiento)

Si el portfolio crece:

```
1. Fase actual (2026): DynamoDB TTL → ~0/mo
2. Fase 2 (100k reads/min): Agregar Momento frente a DynamoDB
   (Momento L1, DynamoDB L2). Costo: $10-20/mo
3. Fase 3 (10M reads/min): Migrar a Redis ElastiCache
   (latencia critica detectada). Costo: $50+/mo + architecture change
```

## Referencias

- AWS: [DynamoDB On-Demand pricing 2026](https://aws.amazon.com/dynamodb/pricing/)
- AWS: [DynamoDB free tier perpetual](https://aws.amazon.com/free/dynamodb/)
- Momento: [Serverless Cache pricing](https://www.gomomento.com/pricing/)
- Momento blog 2025: [Out-caching DAX with serverless solution DynamoDB deserves](https://www.gomomento.com/blog/out-caching-dax-with-the-serverless-solution-dynamodb-deserves/)
- AWS Blog 2023: [All you need to know about caching for serverless applications](https://theburningmonk.com/2019/10/all-you-need-to-know-about-caching-for-serverless-applications/)

