# SPEC-004: Rate-limit module en `common/rate_limit/` + 2 tablas

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/src/common/rate_limit/`,
`rate_limit_rules`, `rate_limit_buckets`, `serverless/template.yaml`
**Dependencias**: SPEC-002 (common), SPEC-003 (cache para rules cacheadas)
**Paralelizable con**: ninguna del nivel (es la base de contact_form y tracking_pixel)

## 1. Contexto

Reemplazo de AWS WAF rate-based rules ($7/mes) con DynamoDB self-managed
($0). Documentado en `.claude/docs/serverless-rate-limit/` (10 docs) +
skill `/serverless-rate-limit`. Sliding window weighted, atomic counters,
auto-blacklist por patron de bot detection.

### Hallazgos de exploracion

- Skill `serverless-rate-limit` validada 5/5 PASS
- Algoritmo definido en `02-sliding-window-weighted-deep-dive.md`
- Codigo Python de referencia en `04-python-implementation.md`

## 2. Solucion propuesta

Crear modulo `common/rate_limit/` con 7 archivos + agregar 2 tablas al
SAM template:

```text
common/rate_limit/
├── __init__.py            # exports: check_or_raise, RateLimitExceededError
├── check.py               # API publica: check_or_raise(ip, endpoint, country, turnstile_validated)
├── rules.py               # Lee rate_limit_rules (cached con @cached ttl=60)
├── buckets.py             # Sliding window weighted + atomic UpdateItem ADD
├── auto_blacklist.py      # Bot detection: 3+ tokens en 60s -> blacklist 24h
├── decisions.py           # TypedDict Decision(allowed, reason, retry_after, status_code)
├── exceptions.py          # RateLimitExceededError, IPBlacklistedError, CountryBlockedError
└── README.md
```

### Decisiones clave

- **Decision 1: Cache de rules con `@cached(ttl=60, stale_for=300)`** —
  rules tabla es read-heavy (cada request hace lookup) write-rare
  (raramente cambia). Cache reduce reads y latencia.
- **Decision 2: NUNCA cachear buckets** — counters deben ser fresh para
  evitar race conditions logicas (cache stale = mas requests permitidos
  del limit real).
- **Decision 3: Atomic ADD en UpdateItem** — DynamoDB garantiza atomic
  increment sin lock. Mas eficiente que GetItem + PutItem con
  ConditionExpression.
- **Decision 4: Reglas iniciales hardcoded** en SPEC, se cargan via
  `serverless rate-limit set` post-deploy:
  - `endpoint#/contact`: limit=3, window=300, action=throttle
  - `endpoint#/track`: limit=30, window=300, action=throttle
  - `endpoint#/validate-turnstile`: limit=5, window=60, action=throttle
  - `endpoint#*` (default fallback): limit=10, window=60

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given IP `1.2.3.4`, endpoint `/contact`, sin reglas previas,
  When invoco `check_or_raise()` 4 veces seguidas con `limit=3`, Then
  las primeras 3 retornan OK y la 4ta levanta `RateLimitExceededError`
  con `retry_after_seconds` calculado
- **AC-2**: Given IP en whitelist (`rule_key=ip#1.2.3.4 kind=ip_whitelist`),
  When invoco `check_or_raise()` 100 veces, Then todas las 100 retornan
  OK sin contar contra bucket
- **AC-3**: Given IP en blacklist, When invoco `check_or_raise()`, Then
  levanta `IPBlacklistedError` inmediatamente sin tocar buckets
- **AC-4**: Given `country#CN kind=country action=block`, When invoco
  con CF-IPCountry=CN, Then levanta `CountryBlockedError`
- **AC-5**: Given IP con 3 invocaciones con `turnstile_validated=True`
  en <60s, When invoco la 4ta, Then auto-blacklist crea
  `rule_key=ip#<addr> kind=ip_blacklist expires_at=now+86400`
- **AC-6**: Given 10 invocaciones concurrentes (threading), When
  ejecutan `check_or_raise()` simultaneamente, Then el counter final
  refleja exactamente 10 (atomic ADD sin race)
- **AC-7**: Given bucket sin acceso por 600s (window 300 + grace 60s),
  When verifico DynamoDB, Then el item se borra automaticamente via
  TTL service

## 4. Diagrama de Flujo

Documentado en `serverless/ARCHITECTURE.md` seccion 4.9.

Resumen:

```text
extract_ip(event)
    -> read rules (cached 60s)
        -> ip whitelist? skip
        -> ip blacklist? raise IPBlacklistedError
        -> country rule? raise CountryBlockedError si block
    -> sliding window check (read 2 buckets: current + previous)
        -> effective_count >= limit? raise RateLimitExceededError
    -> atomic UpdateItem ADD count, turnstile_tokens
    -> auto-blacklist check (turnstile_tokens >= 3 in 60s)
```

## 5. Diagrama ER

Tablas `rate_limit_rules` y `rate_limit_buckets` documentadas en
`serverless/ARCHITECTURE.md` seccion 6. Sin cambios.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN limit=3, IP=A, 4 invocaciones THEN 4ta levanta RateLimitExceededError [AC-1]
- WHEN IP en whitelist THEN 100 invocaciones todas OK [AC-2]
- WHEN IP en blacklist THEN raise IPBlacklistedError sin tocar bucket [AC-3]
- WHEN country=CN action=block THEN raise CountryBlockedError [AC-4]
- WHEN turnstile_tokens=3 en 60s THEN auto-blacklist creado con TTL 24h [AC-5]
- WHEN 10 threads concurrent ADD THEN count final = 10 [AC-6]

### 6.B. Unit Tests (pytest + moto + freezegun)

Path mirror `tests/unit/common/rate_limit/test_<X>.py`:

- `test_check.py` — API publica + integracion entre componentes
- `test_rules.py` — cached lookup con moto
- `test_buckets.py` — sliding window math + atomic ADD
- `test_auto_blacklist.py` — bot detection trigger
- `test_decisions.py` — TypedDict shape
- `test_exceptions.py` — herencia + extra context

Coverage minimo: 90% per-file (modulo critico, primera linea de defensa).

### 6.C. Typecheck

- `serverless typecheck --module-path=src/common/rate_limit` pasa

### 6.D. Integration test

- Stress test local con 100 requests concurrent contra moto DynamoDB —
  verificar que el rate-limit cuenta correctamente sin race conditions.

## 7. Archivos Afectados

### Crear

- `serverless/src/common/rate_limit/__init__.py` — exports
- `serverless/src/common/rate_limit/check.py` — `check_or_raise()`
  - Verificar: AC-1 a AC-5
- `serverless/src/common/rate_limit/rules.py` — cached lookup
  - Verificar: rules cacheadas 60s, miss recarga
- `serverless/src/common/rate_limit/buckets.py` — sliding window weighted
  - Verificar: AC-1, AC-6 + math correcto en edge cases
- `serverless/src/common/rate_limit/auto_blacklist.py` — bot detection
  - Verificar: AC-5
- `serverless/src/common/rate_limit/decisions.py` — TypedDict
- `serverless/src/common/rate_limit/exceptions.py` — error hierarchy
- `serverless/src/common/rate_limit/README.md` — quick start + algoritmo

### Modificar

- `serverless/template.yaml` — agregar 2 tablas (`RateLimitRulesTable`,
  `RateLimitBucketsTable`) con TTL habilitado segun
  `ARCHITECTURE.md` seccion 7
  - Verificar: `serverless validate` + `serverless deploy --stage=dev`
- `serverless/src/common/__init__.py` — re-exportar `check_or_raise`

### Tareas post-deploy

- Cargar reglas iniciales via CLI:

```bash
serverless rate-limit set --endpoint=/contact --limit=3 --window=300 \
    --action=throttle --reason="Form contacto MVP"

serverless rate-limit set --endpoint=/track --limit=30 --window=300 \
    --action=throttle --reason="Tracking pixel MVP"

serverless rate-limit set --endpoint=/validate-turnstile --limit=5 \
    --window=60 --action=throttle --reason="Internal endpoint"

serverless rate-limit list  # verificar 3 reglas creadas
```

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | decisions.py + exceptions.py | — | T2, T3 |
| T2 | rules.py | T1 + cache module (SPEC-003) | T3 |
| T3 | buckets.py | T1 | T2 |
| T4 | auto_blacklist.py | T1 + T2 | — |
| T5 | check.py (integra todo) | T1-T4 | — |
| T6 | template.yaml update + deploy | T5 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-002 done (common module)
- [ ] SPEC-003 done (cache module, requerido para `@cached` en rules)
- [ ] Stack desplegado con `cache` table funcionando

### Definition of Done

- [ ] AC-1 a AC-7 cumplidos
- [ ] Coverage >= 90% per-file
- [ ] mypy --strict pasa
- [ ] Stress test 100 concurrent requests sin race conditions
- [ ] Latencia warm de `check_or_raise`: p99 < 30ms
- [ ] 3 reglas iniciales cargadas y verificables con
      `serverless rate-limit list`
- [ ] Skill `/serverless-rate-limit` se invoca para preguntas
