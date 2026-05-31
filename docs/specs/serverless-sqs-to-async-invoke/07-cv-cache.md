# 07 — cv: `@cached` DynamoDB (el mayor impacto absoluto)

[← 06 encoders](06-encoders-refactor.md) · [siguiente: 08 migrar callers →](08-migrate-callers-remove-sqs.md)

> Fase 5. El fix de mayor impacto absoluto del plan. `cv` es read-only y casi
> estático, pero hoy hace un **fan-out de ~11 queries a Neon en CADA request**
> (warm 7.3s medido en CloudWatch). La tabla `cache` ya está provisionada en su
> manifest pero **NUNCA se usa**. Cachear con `@cached` (DynamoDB TTL+SWR, el
> módulo `shared/cache/` ya existe) elimina el toque a Neon en cache hit.

## 7.1 Smoking gun (HECHO verificado)

- `cv/manifest.yaml` declara `uses.tables.cache: read-write` + el env var SSM
  del nombre de la tabla → la cache **está provisionada**.
- `rg cached serverless/lambda/services/cv/` → **0 resultados en el código**
  (sólo el comentario en `config.py`). `cv_repository.py` tiene 0 `@cached`.
- Resultado: `cv.get` ejecuta `get_full_cv()` ([cv_repository.py:840]) que
  encadena ~11 funciones `list_*`/`get_*`, cada una con su(s) query(s) a Neon →
  7.3s warm, 10.1s cold (Restore 1.2s ya es óptimo).

→ La infra de cache existe y está pagada; sólo falta **usarla**.

## 7.2 Diseño

Cachear en el nivel del **agregador por (action, niche, locale)**, NO query por
query (un solo `GetItem` sirve la respuesta entera):

```python
# cv/core/services/cv_service.py (o donde se orqueste cv.get)
from shared.cache import cached   # decorator ya existente

@cached(ttl=900, namespace='cv', stale_for=86400, tags=['cv'])
def get_cv_payload(*, action: str, niche: str | None, locale: str) -> dict:
    # delega en cv_repository (Neon) SOLO en cache miss
    ...
```

- `ttl=900` (15 min): el CV cambia raro; 15 min es conservador. Ajustable.
- `stale_for=86400` (24h SWR): si expira, sirve stale y NO bloquea (en Lambda
  el refresh async es frágil — el decorator sirve stale, ver
  `shared/cache/decorator.py:16-17`). El visitante NUNCA espera el fan-out.
- `tags=['cv']`: permite invalidar TODA la cache del CV de un golpe al
  re-seedear (la Lambda `db` con `command=seed` debe llamar
  `invalidate_by_tag('cv')` tras actualizar el CV).
- `namespace='cv'` + el hash de `(action, niche, locale)` arman la cache key
  (el decorator hashea args/kwargs, `decorator.py:50`).

### Por action o sólo cv.get

`cv.get` es el caso de 7.3s (fan-out de las 11 secciones). Las demás actions
(`cv.profile`, `cv.experiences`, ...) ya son 0.7-1.4s warm (1 query). Decisión:
**cachear las que tocan Neon** — todas las `cv.*` de lectura — con la misma
firma; cada una su key. El mayor impacto es `cv.get`, pero cachear todas es
barato y uniforme.

## 7.3 Invalidación (al re-seedear el CV)

El CV se actualiza por el seed (YAML → Neon, lo corre la Lambda `db` con
`command=seed`). Tras seedear, invalidar:

```python
from shared.cache import invalidate_by_tag
invalidate_by_tag('cv')   # purga todas las entradas tag='cv'
```

- Agregar este paso al final del `seed_service` de la Lambda `db`.
- **SIEMPRE** invalidar tras el seed; sino el CV viejo persiste hasta el TTL.

## 7.4 Lazy del path Neon en cache hit (bonus de cold, opcional)

En cache HIT, `cv` no necesita Neon → no necesita `shared.db`/sqlalchemy. PERO:
con SnapStart, `shared.db` ya está en el snapshot (Restore 1.2s, no se re-paga).
Sacarlo del module-scope lo movería al cache-miss handler (CPU-starved) →
**NO conviene** (mismo razonamiento que la regla anti-lazy del README). Mantener
`shared.db` eager + warm_db en INIT. El ahorro del cache es por **no tocar
Neon** (wake + query), no por imports.

## 7.5 Impacto esperado (a confirmar en fase 8 con CloudWatch)

| Métrica cv.get | Antes | Después (cache hit) |
|----------------|------:|--------------------:|
| Handler warm | 7.3s | **< 0.1s** (GetItem DynamoDB ~10ms) |
| Handler cold | 10.1s | **~Restore (1.2s)** + GetItem (no wake Neon) |
| Roundtrip api_e2e cold | 13.9s | **~4s** (1.2 restore + red ~2.6) |

DynamoDB On-Demand NO tiene scale-to-zero → responde single-digit ms siempre,
sin wake. Costo $0 (free tier).

## 7.6 Tests (TDD primero)

- `cv/tests/unit/test_cv_get_uses_cache_on_hit.py` — Given una entrada en cache
  para `(get, niche, locale)`, When `get_cv_payload`, Then devuelve el valor
  cacheado y NO llama a `cv_repository` (mock del repo, assert 0 llamadas).
- `..._cache_miss_queries_neon_and_populates.py` — Given cache vacía, When se
  llama, Then consulta el repo UNA vez y escribe la entrada (assert exacto).
- `..._seed_invalidates_cv_tag.py` (en la Lambda `db`) — Given el seed corre,
  Then llama `invalidate_by_tag('cv')` exactamente una vez.

## Archivos afectados (fase 5)

### Crear
- `serverless/lambda/services/cv/core/services/cv_service.py` (o ampliar el
  existente) — `get_cv_payload` con `@cached`.
  - Verificar: `serverless tests --type=unit --lambda=cv` (≥80%).
- tests unit arriba.

### Modificar
- `cv/core/controllers/<cv actions>` — llamar `get_cv_payload` cacheado en vez
  de `cv_repository` directo.
- `serverless/lambda/services/db/core/services/seed_service.py` —
  `invalidate_by_tag('cv')` al final del seed.
  - Verificar: `serverless lint-deps --lambda=cv` exit 0; `--lambda=db`.

[← 06 encoders](06-encoders-refactor.md) · [siguiente: 08 migrar callers →](08-migrate-callers-remove-sqs.md)
