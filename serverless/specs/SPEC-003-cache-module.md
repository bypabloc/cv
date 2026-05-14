# SPEC-003: Cache module en `common/cache/` + tabla `cache`

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/src/common/cache/`, tabla DynamoDB `cache`
**Dependencias**: SPEC-002
**Paralelizable con**: SPEC-007 (no dependen)

## 1. Contexto

Las 5 Lambdas leen valores caros que cambian poco: SSM secrets, country
lookups, queries agregadas Neon, UA parsing. Sin cache, cada invocacion
los re-fetcha. La skill `dynamodb-cache` consolida el patron correcto:
DynamoDB TTL + lock distribuido + SWR + tag invalidation.

### Hallazgos de exploracion

- 8 docs en `.claude/docs/dynamodb-cache/` con implementacion completa
- Skill `/dynamodb-cache` para preguntas durante implementacion
- Tabla `cache` ya definida en SPEC-001 (no requiere cambios en template)

## 2. Solucion propuesta

Crear `serverless/src/common/cache/` con 9 archivos siguiendo el codigo
de referencia en `.claude/docs/dynamodb-cache/06-python-implementation.md`:

```text
common/cache/
├── __init__.py          # exports: DynamoDBCache, cached, CacheStatus
├── client.py            # class DynamoDBCache (get/set/delete/invalidate/lock)
├── decorator.py         # @cached(ttl, namespace, stale_for, tags)
├── swr.py               # fresh|stale|expired states
├── stampede.py          # Lock distribuido + XFetch probabilistic
├── invalidation.py      # Tag-based bulk invalidation
├── serializers.py       # JSON + bytes_b64 fallback
├── types.py             # CacheEntry, CacheStatus
└── README.md            # patterns + cuando usar SWR
```

### Decisiones clave

- **Decision 1: Generic key-value (no especifico a Turnstile)** — confirmed
  en pregunta previa al user. API uniforme `cache.get/set/delete`.
- **Decision 2: Lock con DynamoDB ConditionalWrite** — vs Redis SETNX o
  ElastiCache. Razon: 1 menos servicio, free tier perpetuo, $0 idle.
- **Decision 3: Stale-while-revalidate via threading.Thread (no asyncio)** —
  Lambda Python no es async-first y `asyncio.create_task` en Lambda
  context puede no completar antes del shutdown. Thread daemon=True con
  cleanup en `atexit`.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given decorator `@cached(ttl=300)`, When invoco la funcion
  warm 2 veces, Then segunda invocacion lee de DynamoDB sin recomputar
  (cache HIT) y retorna mismo valor
- **AC-2**: Given decorator `@cached(ttl=60, stale_for=300)` y valor
  expirado (now > expires_at, now < stale_until), When invoco, Then
  retorna valor stale inmediatamente + dispara refresh async
- **AC-3**: Given 10 Lambdas concurrentes invocando la misma funcion con
  cache expirado, When ejecuto, Then SOLO 1 Lambda recomputa (lock
  distribuido) + las otras 9 obtienen el valor del nuevo cache o stale
- **AC-4**: Given items con `tags=['secrets']`, When llamo
  `cache.invalidate(tag='secrets')`, Then todos los items con ese tag
  tienen `expires_at = 0` (soft delete) en max 5 segundos
- **AC-5**: Given item con TTL=60s, When pasa 60s sin acceso, Then AWS
  DynamoDB elimina el item dentro de 48h (TTL service) sin consumir WCU
- **AC-6**: Given lock holder hace cold start largo (10s) y mueren antes
  de release, When otro Lambda intenta acquire_lock, Then despues de
  `lock_expires` (15s default) puede adquirir el lock (no deadlock)

## 4. Diagrama de Flujo

```text
@cached(ttl=300, stale_for=600, namespace='ssm', tags=['secrets'])
def get_turnstile_secret() -> str: ...

    Caller
        |
        v
    DynamoDBCache.get(key)
        |
        +-- fresh (now < expires_at)
        |       -> return cached value
        |
        +-- stale (expires_at < now < stale_until)
        |       -> return cached + threading.Thread(_refresh_async)
        |
        +-- expired (now >= stale_until) o miss
                |
                v
        acquire_lock(key, ttl=15s)
                |
            +-+-+
            | OK     | NO
            v        v
            compute  busy-wait 500ms, return stale
            |
            v
        result = fn(...)
        set(key, result, ttl, tags)
            (incluye release lock + expires_at + stale_until)
            |
            v
        return result
```

## 5. Diagrama ER

Tabla `cache` ya documentada en `serverless/ARCHITECTURE.md` seccion 6.5.
Sin cambios en estructura.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN cache.get(missing_key) THEN retorna None [AC-1]
- WHEN cache.set(key, value, ttl=60) seguido de cache.get(key) THEN retorna value [AC-1]
- WHEN cache esta stale (mock time) THEN @cached devuelve stale + spawnea thread [AC-2]
- WHEN 2 threads compiten por lock THEN solo 1 adquiere [AC-3]
- WHEN cache.invalidate(tag='secrets') THEN items con ese tag expires_at=0 [AC-4]
- WHEN lock holder expira lock_expires THEN nuevo holder puede adquirir [AC-6]

### 6.B. Unit Tests (pytest + moto)

Path mirror `tests/unit/common/cache/test_<X>.py`:

- `test_client.py` — get/set/delete/invalidate con moto DynamoDB
- `test_decorator.py` — `@cached` aplicado a funcion mock
- `test_swr.py` — transitions fresh/stale/expired
- `test_stampede.py` — race conditions simuladas con threading
- `test_invalidation.py` — bulk tag invalidation
- `test_serializers.py` — JSON + bytes serializacion roundtrip

Coverage minimo: 85% per-file (codigo concurrente, dificil cubrir
todas las branches).

### 6.D. E2E (opcional, deploy + cache real)

- Deploy stack dev. Invocar `cache.set` desde Lambda contact-form de
  prueba, esperar TTL expire, verificar AWS borra item dentro de 48h.

## 7. Archivos Afectados

### Crear

- `serverless/src/common/cache/__init__.py` — exports publicos
  - Verificar: `python -c "from common.cache import cached, DynamoDBCache"` ok
- `serverless/src/common/cache/client.py` — `class DynamoDBCache`
  - Verificar: AC-1, AC-4 + tests
- `serverless/src/common/cache/decorator.py` — `@cached`
  - Verificar: AC-1, AC-2 + tests
- `serverless/src/common/cache/swr.py` — SWR state machine
  - Verificar: AC-2 + tests
- `serverless/src/common/cache/stampede.py` — lock + XFetch
  - Verificar: AC-3, AC-6 + tests
- `serverless/src/common/cache/invalidation.py` — `cache.invalidate(tag)`
  - Verificar: AC-4 + tests
- `serverless/src/common/cache/serializers.py` — JSON + bytes
- `serverless/src/common/cache/types.py` — TypedDicts
- `serverless/src/common/cache/README.md` — quick start

### Modificar

- `serverless/src/common/__init__.py` — re-exportar `cache.cached` para
  acceso ergonomico `from common import cached`

## 8. Descomposicion para Paralelizacion

Dependencias internas: `decorator.py` depende de `client.py + swr.py +
stampede.py`. Por tanto:

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | types.py + serializers.py | — | T2, T3 |
| T2 | client.py (CRUD basico) | T1 | T1 |
| T3 | stampede.py (lock) | T2 | T4 |
| T4 | swr.py + invalidation.py | T2 | T3 |
| T5 | decorator.py (combina todo) | T2, T3, T4 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-002 done (`common/` modulo existe)
- [ ] Tabla `cache` desplegada (SPEC-001)

### Definition of Done

- [ ] AC-1 a AC-6 cumplidos
- [ ] Coverage >= 85% per-file
- [ ] mypy --strict pasa
- [ ] Cache hit latency p99 < 15ms (medible en X-Ray)
- [ ] Cache miss + compute + set latency p99 < 100ms (sin contar fn user)
- [ ] Documentacion en `.claude/docs/dynamodb-cache/06-python-implementation.md`
      esta sincronizada con el codigo final (review manual)
- [ ] Skill `/dynamodb-cache` se invoca para preguntas de uso
