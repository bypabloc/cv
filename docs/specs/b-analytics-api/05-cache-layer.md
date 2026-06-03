# 05 — Capa de cache

[< 04-queries-sql](04-queries-sql.md) | [Siguiente: 06-testing >](06-testing.md)

> Decisiones de cache para el Lambda `analytics`: que se cachea, con que
> TTL, claves, tags, e invalidacion. Reusa `shared.cache` (DynamoDB
> table `portfolio-cache-<stage>` con TTL nativo + lock distribuido +
> stale-while-revalidate).

## 1. Estrategia general

| Categoria | Endpoints | TTL | Justificacion |
|-----------|-----------|-----|---------------|
| Agregada estandar | overview, top-pages, top-referrers, top-niches, retention, events/distribution, events/heatmap, visits/landing-pages, geo/by-country, devices/breakdown, funnel/conversion, contacts/by-status | 60s | Refrescos del dashboard < 60s no impactan Neon |
| Agregada timeseries | analytics/timeseries | 60s | Idem |
| Live | analytics/active-now | 10s | Casi-realtime sin saturar Neon |
| Listado crudo | events/list, sessions/list, sessions/detail, visits/list, contacts/list | NO cache | Filtros distintos por request; cachear no ayuda |

## 2. Como aplicar `@cached`

`shared.cache.decorator.cached` es un decorator. Patron exacto del repo:

```python
from shared.cache.decorator import cached

@cached(ttl=60, namespace='analytics:overview', tags=['analytics-aggregate'])
def overview(*, date_from: date, date_to: date) -> dict[str, Any]:
    ...
```

Reglas duras:

- **SIEMPRE** keyword-only args en funciones cacheadas. El decorator
  serializa `kwargs` para construir la clave; positional args harian
  llaves distintas para llamadas equivalentes.
- **SIEMPRE** los args deben ser tipos primitivos serializables
  (`str`, `int`, `bool`, `date`, `None`). Pasar un `_Meta` o un
  `Session` como kwarg ROMPE la serializacion.
- **SIEMPRE** namespace = `analytics:<action>` (kebab-case mantenido).
- **SIEMPRE** tags = `['analytics-aggregate']` (mas tags especificos
  si aplica). Permite invalidacion por tag.
- **NUNCA** cachear listados crudos (page=2 con filtros distintos = key
  diferente, pero cada filtro raro corre 1 query nueva igual; el
  espacio cache se llena sin beneficio).
- **NUNCA** cachear `sessions/detail` — un session puede llegar a tener
  N visits y M events, no es paginado, el filtro es `session_id` unico.
- **NUNCA** poner `IP` o `country` del visitante en la clave de cache.
  La data de analytics es global, no por-IP del que consulta.

## 3. Composicion de claves

`shared.cache.cached` arma la clave asi:

```text
cache_key = SHA256(namespace || ":" || canonical_kwargs)[0:16]
```

Donde `canonical_kwargs` es JSON ordenado por key de los kwargs.

Para `overview(date_from=2026-04-27, date_to=2026-05-27)`:

```text
namespace = "analytics:overview"
kwargs    = {"date_from": "2026-04-27", "date_to": "2026-05-27"}
key       = SHA256("analytics:overview:{\"date_from\":\"2026-04-27\",...}")[0:16]
```

Esto significa: dos requests identicas (mismas dates) -> mismo cache
key -> hit. Dos requests con dates distintas -> miss.

## 4. Tags e invalidacion

Tags permiten invalidar grupos de keys con `shared.cache.invalidate_tag()`.

| Tag | Que invalida | Cuando invalidar |
|-----|--------------|------------------|
| `analytics-aggregate` | TODAS las queries agregadas | Manual via Lambda `db` con command nuevo si fuera necesario (NO automatico) |
| `analytics-overview` | Solo overview | Idem (no implementado en este plan) |
| `analytics-funnel` | Solo funnel | Idem |

**Decision**: NO invalidar automaticamente. El TTL 60s ya da freshness
suficiente. Si en el futuro el dashboard necesita "force refresh", se
agrega un command en la Lambda `db`:

```bash
serverless run --stage=dev --lambda=db \
  --event=events/invalidate_analytics_cache.json
```

Con payload `{"command": "cache-invalidate", "args": {"tag":
"analytics-aggregate"}}`.

## 5. Cache para `active-now`

TTL 10s. Razon:

- `active-now` es "live counter" — el dashboard puede refrescarlo cada
  5-10s para feedback visual.
- Sin cache: 1 query a Neon cada 5s = 12 queries/min/cliente.
- Con TTL 10s: maximo 6 queries/min/cliente (mitad del trafico DB).
- Trade-off: el counter puede estar hasta 10s atrasado. Aceptable para
  un dashboard de un visitante (no es ticker de bolsa).

```python
from datetime import datetime, timezone
from typing import Any

from shared.cache.decorator import cached
from shared.db.models.visitor.session import Session as VisitorSession
from shared.db.sa import func, select
from shared.db.session import db_session

@cached(ttl=10, namespace='analytics:active-now', tags=['analytics-live'])
def active_now() -> dict[str, Any]:
    with db_session() as s:
        active = s.scalar(
            select(func.count())
            .select_from(VisitorSession)
            .where(VisitorSession.last_seen_at >= func.now() - func.make_interval(mins=5))
        )
    return {
        'active_sessions': int(active or 0),
        'threshold_minutes': 5,
        'as_of': datetime.now(timezone.utc).isoformat(),
    }
```

NOTAS:

- `datetime.now(timezone.utc)` reemplaza al deprecado `datetime.utcnow()`
  (DeprecationWarning desde Python 3.12). `isoformat()` ya emite el
  sufijo `+00:00`; no se concatena `'Z'` para evitar duplicacion del
  marcador UTC.
- `func.make_interval(mins=5)` es equivalente a `make_interval(0,0,0,0,0,5,0)`
  pero legible: solo el argumento relevante por nombre.

NOTA: la function `now()` se evalua en Neon, asi que el cache es
correcto durante 10s, despues miss y nueva eval.

## 6. Que NO se cachea — racionales individuales

### `events/list`

- Filtros por session_id, page_path, niche, event_type con N
  combinaciones.
- Pagina N con filtro X cambia con cada visit nuevo (`ORDER BY
  created_at DESC`).
- Cachear 60s significa que la primera pagina puede no mostrar la
  ultima visita. Mala UX para listado.

### `sessions/list`

- Idem `events/list`. Ademas el orden es por `last_seen_at DESC` que
  cambia minuto a minuto.

### `sessions/detail`

- Una session por request. La data de una session especifica casi no
  cambia (solo si el visitante vuelve mientras se consulta).
- Cachear seria correcto pero el espacio es proporcional al numero de
  sessions consultadas — el dashboard lista N sessions, usuario clickea
  uno, raramente el mismo. ROI bajo.

### `visits/list` y `contacts/list`

- Mismos argumentos que `events/list`.

## 7. Cold cache vs warm cache

Primera invocacion del dia (cold cache + cold Lambda):

```
SnapStart Restore     ~ 800ms
Handler init          ~ 0ms (warm via SnapStart)
extract_request       ~ 5ms
guard (rate-limit)    ~ 20ms (1 DynamoDB GetItem rule + Query bucket)
service.overview      ~ 200ms (cache miss + 7 SQL queries)
serialize             ~ 5ms
TOTAL primera req     ~ 1030ms
```

Segunda invocacion misma query (warm cache + warm Lambda):

```
extract_request       ~ 5ms
guard (rate-limit)    ~ 15ms
@cached (hit)         ~ 15ms (1 DynamoDB GetItem)
serialize             ~ 5ms
TOTAL                 ~ 40ms
```

Segunda invocacion con cache miss (warm Lambda, cache expirado):

```
extract_request       ~ 5ms
guard (rate-limit)    ~ 15ms
@cached miss + DB     ~ 200ms
@cached set           ~ 10ms (background, no bloquea)
serialize             ~ 5ms
TOTAL                 ~ 225ms
```

## 8. Observabilidad del cache

Cada acceso al cache emite metric:

- `AnalyticsCacheHit` (dimensions: Operation, Action) — incrementa en hit
- `AnalyticsCacheMiss` (dimensions: Operation, Action) — incrementa en miss

Metric implicito que ya emite `shared.cache`:

- `CacheHit` / `CacheMiss` con dimension `Namespace`

Logs estructurados (level INFO):

```json
{
  "level": "INFO",
  "message": "cache hit",
  "namespace": "analytics:overview",
  "cache_key": "ab12cd34ef567890",
  "ttl_remaining_sec": 42
}
```

```json
{
  "level": "INFO",
  "message": "cache miss",
  "namespace": "analytics:overview",
  "cache_key": "ab12cd34ef567890",
  "computed_in_ms": 187
}
```

## 9. Cache stampede prevention

`shared.cache` usa lock distribuido con `ConditionExpression` en
DynamoDB. Cuando 2 requests llegan al mismo tiempo con el mismo key:

1. Request A: cache miss -> intenta `PutItem(lock_key,
   ConditionExpression='attribute_not_exists(lock_key)')` -> exito.
2. Request B: cache miss -> intenta el mismo `PutItem` -> falla
   (`ConditionalCheckFailedException`) -> espera 100ms y reintenta cache
   read.
3. Request A: computa la query (~200ms) -> guarda en cache -> libera
   lock.
4. Request B (despues de 100ms): cache hit -> retorna.

Asi 100 requests concurrentes a `overview` resultan en 1 sola query a
Neon, no 100. Probado en el repo con `tracking_pixel`.

## 10. Tabla DynamoDB `portfolio-cache-<stage>`

Schema (ya existe, no se modifica):

```yaml
hash_key:      cache_key  (S)
ttl_attribute: expires_at (N — Unix epoch seconds)
billing_mode:  PAY_PER_REQUEST
```

Items que escribimos:

```json
{
  "cache_key":  "ab12cd34ef567890",
  "namespace":  "analytics:overview",
  "tags":       ["analytics-aggregate"],
  "value":      "{\"sessions\":123,\"visits\":...}",
  "created_at": "2026-05-27T14:00:00Z",
  "expires_at": 1748358060,
  "lock_owner": null
}
```

Lock items (efimeros, TTL ~5s):

```json
{
  "cache_key":  "ab12cd34ef567890::lock",
  "lock_owner": "<request_id>",
  "expires_at": 1748357065
}
```

## 11. Tamano estimado del cache

| Endpoint | items teoricos | items reales | tamano/item | total |
|----------|----------------|--------------|-------------|-------|
| overview | infinitos (rangos de date) | ~30 unicos/dia | ~500 B | 15 KB/dia |
| timeseries | mismo orden | ~50/dia | ~3 KB | 150 KB/dia |
| top-* | mismo orden | ~30/dia | ~1 KB | 30 KB/dia |
| heatmap | pocos | ~10/dia | ~5 KB | 50 KB/dia |
| funnel | mismo orden | ~10/dia | ~500 B | 5 KB/dia |
| active-now | 1 unico | TTL 10s, ~8640/dia escrituras | ~200 B | 2 KB/dia |
| **Total** | | | | **~250 KB/dia** |

DynamoDB free tier: 25 GB storage. El cache ocupa <0.001% del free tier.
TTL nativo borra items vencidos sin costo.

## 12. Helpers de testing

Para tests unit, mockear el decorator requiere cuidado: `@cached` se aplica
en **import-time** del modulo del service, por lo que hacer
`monkeypatch.setattr('shared.cache.decorator.cached', ...)` DESPUES de que
el service ya fue importado no tiene efecto sobre las funciones ya decoradas.

El patron correcto (consistente con `06-testing`):

- **Parchear ANTES de importar el service** dentro del test. Usar
  `monkeypatch.setattr` en un fixture de `autouse=False` y realizar el
  `import` del modulo del service DENTRO del cuerpo del test (o del fixture),
  no en el nivel de modulo del archivo de test.
- En `tests/integration/`: usar la tabla real (test stage) con un
  namespace de prefijo unico (`analytics-test:overview`) para no
  colisionar con prod.

Implementacion del bypass:

```python
# tests/conftest.py  (o en el archivo de test que lo necesite)
import pytest

@pytest.fixture
def no_cache(monkeypatch):
    """
    Reemplaza @cached por un passthrough para tests unit.

    IMPORTANTE: el modulo del service que usa @cached debe importarse
    DESPUES de que este fixture haya parcheado shared.cache.decorator.cached,
    es decir, dentro del cuerpo del test (o de un fixture posterior), no en el
    nivel de modulo del archivo de test. Si ya se importo, el patch no tiene
    efecto sobre las funciones ya decoradas.
    """
    def _passthrough(*decorator_args, **decorator_kwargs):
        def _wrap(fn):
            return fn  # sin cache, pasa directo
        return _wrap

    monkeypatch.setattr('shared.cache.decorator.cached', _passthrough, raising=True)
```

Ejemplo de uso correcto en un test:

```python
def test_overview_returns_expected_shape(no_cache):
    # El service se importa AQUI, despues de que no_cache haya parcheado cached.
    from core.services.analytics_service import overview  # noqa: PLC0415

    result = overview(date_from=date(2026, 1, 1), date_to=date(2026, 1, 31))
    assert result['sessions'] >= 0
```

Si el import del service ocurre en el nivel de modulo del archivo de test,
usar `importlib.reload` dentro del fixture para que el modulo re-aplique el
decorator ya parcheado.

[< 04-queries-sql](04-queries-sql.md) | [Siguiente: 06-testing >](06-testing.md)
