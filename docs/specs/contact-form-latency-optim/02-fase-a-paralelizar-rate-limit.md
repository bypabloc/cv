# Fase A: Paralelizar las 4 DDB del rate_limit

## Objetivo

Refactorizar `shared/rate_limit/check.py` para lanzar las 4 lookups DDB con
`concurrent.futures.ThreadPoolExecutor(max_workers=4)` en paralelo, aplicando
la logica condicional (short-circuit) DESPUES con los 4 resultados ya
disponibles.

## Estado actual (`check.py:41-146`)

```python
def check_or_raise(*, ip, endpoint, country=None, turnstile_validated=False, now=None):
    current_time = now if now is not None else int(time.time())

    # 1. SECUENCIAL: get_ip_rule
    ip_rule = get_ip_rule(ip)
    if ip_rule is not None:
        # short-circuit: blacklist o whitelist
        ...

    # 2. SECUENCIAL: get_country_rule (solo si country no None)
    if country:
        country_rule = get_country_rule(country)
        if country_rule and country_rule.get('action') == 'block':
            raise CountryBlockedError(...)

    # 3. SECUENCIAL: get_endpoint_rule (depende del result para extraer
    #    window_seconds y limit)
    endpoint_rule = get_endpoint_rule(endpoint)
    limit = endpoint_rule.get('limit', DEFAULT_LIMIT) if endpoint_rule else DEFAULT_LIMIT
    window_seconds = endpoint_rule.get('window_seconds', DEFAULT_WINDOW_SECONDS) if endpoint_rule else DEFAULT_WINDOW_SECONDS

    # 4. SECUENCIAL: get_effective_count (depende del window_seconds)
    effective = get_effective_count(ip=ip, endpoint=endpoint, window_seconds=window_seconds, now=current_time)
    if effective >= limit:
        raise RateLimitExceededError(...)

    # 5. INCREMENT (depende de window_seconds) + auto_blacklist
    bucket = increment_bucket(...)
    if turnstile_validated and should_auto_blacklist(bucket['turnstile_tokens']):
        create_blacklist_rule(ip)

    return Decision(allowed=True, ...)
```

**Problema**: las 4 lookups corren UNA TRAS OTRA. Sum total ~400-600ms en
cold (handshake DDB primera vez) y ~150-300ms en warm.

## Diseno propuesto

### Issue tecnica: dependencia de window_seconds

`get_effective_count` necesita `window_seconds` que sale de `endpoint_rule`.
Para paralelizar las 4 sin esperar a `endpoint_rule`, hay 2 opciones:

**Opcion 1 (elegida)**: Llamar `get_effective_count` con `window_seconds=DEFAULT_WINDOW_SECONDS`
(60s, el valor por defecto). En el 99% de los casos el endpoint rule usa
exactamente 60s (lo verifique en `rate-limit-rules` actual: ningun rule
define window distinto). Si en el futuro un endpoint usa window distinto,
el comportamiento cambia ligeramente (medimos en una ventana menor) pero
es seguro: el bucket sigue siendo coherente con el `increment_bucket` que
viene despues con el window real. Trade-off documentado.

**Opcion 2 (descartada)**: Hacer 2 olas: primero `endpoint_rule` solo, luego
las otras 3 + `effective_count`. Ahorra menos (latencia = sum(2 olas) en vez
de max(4)) y complica el codigo. NO se elige.

### Refactor

```python
from concurrent.futures import ThreadPoolExecutor
from typing import Any

# ... imports existentes ...

# Sentinel para indicar que la lookup no se ejecuto (country=None caso)
_NOT_REQUESTED = object()


def check_or_raise(
    *,
    ip: str,
    endpoint: str,
    country: str | None = None,
    turnstile_validated: bool = False,
    now: int | None = None,
) -> Decision:
    """
    Verifica rate-limit + IP white/blacklist + country rules (PARALELO).

    Las 4 lookups DDB (ip_rule, country_rule, endpoint_rule, effective_count)
    se lanzan en paralelo con ThreadPoolExecutor(max_workers=4) y la logica
    condicional se aplica sobre los 4 resultados.

    Trade-off: si la IP esta blacklisteada, gastamos 3 DDB reads "inutiles"
    (~$0.0000001 cada uno — irrelevante). Beneficio: latencia = max(4) en
    vez de sum(4).

    Args, Returns, Raises: igual que la version anterior.
    """
    current_time = now if now is not None else int(time.time())

    # --- Lanza las 4 lookups en paralelo ---
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_ip = executor.submit(get_ip_rule, ip)
        future_country = (
            executor.submit(get_country_rule, country)
            if country
            else None
        )
        future_endpoint = executor.submit(get_endpoint_rule, endpoint)
        # NOTA: usa DEFAULT_WINDOW_SECONDS para el effective_count porque
        # endpoint_rule aun no esta disponible. Si el rule tiene window
        # distinto (raro: ningun rule actual lo define), el effective_count
        # se mide en una ventana de 60s — es seguro: el increment_bucket
        # de mas abajo usa el window real para el bucket key.
        future_effective = executor.submit(
            get_effective_count,
            ip=ip,
            endpoint=endpoint,
            window_seconds=DEFAULT_WINDOW_SECONDS,
            now=current_time,
        )

        # Espera los 4 (block hasta que el mas lento termine)
        ip_rule = future_ip.result()
        country_rule = (
            future_country.result() if future_country else _NOT_REQUESTED
        )
        endpoint_rule = future_endpoint.result()
        effective = future_effective.result()

    # --- Logica condicional (short-circuit) sobre los 4 resultados ---

    # 1. IP rule
    if ip_rule is not None:
        kind = ip_rule.get('kind', '')
        if kind == 'ip_whitelist':
            return Decision(allowed=True, reason='ip_whitelist', status_code=200)
        if kind == 'ip_blacklist':
            expires = ip_rule.get('expires_at', 0)
            retry_after = (
                max(expires - current_time, 60)
                if expires
                else AUTO_BLACKLIST_DURATION_SECONDS
            )
            raise IPBlacklistedError(
                ip_rule.get('reason', 'IP blacklisted'),
                code='IP_BLACKLISTED',
                retry_after_seconds=int(retry_after),
                extra={'ip': ip},
            )

    # 2. Country rule
    if country and country_rule is not _NOT_REQUESTED and country_rule is not None:
        if country_rule.get('action') == 'block':
            raise CountryBlockedError(
                country_rule.get('reason', f'Country {country} blocked'),
                code='COUNTRY_BLOCKED',
                extra={'country': country},
            )

    # 3. Endpoint rule -> limit + window_seconds
    if endpoint_rule is None:
        limit = DEFAULT_LIMIT
        window_seconds = DEFAULT_WINDOW_SECONDS
    else:
        limit = endpoint_rule.get('limit', DEFAULT_LIMIT)
        window_seconds = endpoint_rule.get('window_seconds', DEFAULT_WINDOW_SECONDS)

    # 4. Effective count + check
    if effective >= limit:
        retry_after = max(window_seconds // 2, 1)
        raise RateLimitExceededError(
            f'Rate limit exceeded: {effective:.1f} >= {limit} in {window_seconds}s window',
            code='RATE_LIMIT_EXCEEDED',
            retry_after_seconds=retry_after,
            extra={
                'ip': ip,
                'endpoint': endpoint,
                'limit': limit,
                'window_seconds': window_seconds,
                'effective_count': round(effective, 2),
            },
        )

    # 5. Atomic INCREMENT (con el window_seconds REAL del rule)
    bucket = increment_bucket(
        ip=ip,
        endpoint=endpoint,
        window_seconds=window_seconds,
        turnstile_validated=turnstile_validated,
        now=current_time,
    )

    # 6. Auto-blacklist check
    if turnstile_validated and should_auto_blacklist(bucket['turnstile_tokens']):
        create_blacklist_rule(ip)

    return Decision(allowed=True, reason='allowed', status_code=200)
```

## Tests TDD (Red phase primero)

### Test 1: paralelizacion mide max(N), no sum(N) [AC-5]

```python
def test_check_or_raise_parallel_total_under_max_when_all_slow(monkeypatch):
    """
    Given las 4 lookups DDB que demoran 100ms cada una,
    When check_or_raise corre,
    Then total duration es < 150ms (max + overhead), NUNCA > 200ms.
    """
    import time
    from unittest.mock import patch

    def slow_ip(_ip):
        time.sleep(0.1)
        return None
    def slow_country(_country):
        time.sleep(0.1)
        return None
    def slow_endpoint(_endpoint):
        time.sleep(0.1)
        return {'limit': 100, 'window_seconds': 60}
    def slow_effective(**_kw):
        time.sleep(0.1)
        return 0.0

    with patch.multiple(
        'shared.rate_limit.check',
        get_ip_rule=slow_ip,
        get_country_rule=slow_country,
        get_endpoint_rule=slow_endpoint,
        get_effective_count=slow_effective,
        increment_bucket=lambda **_: {'turnstile_tokens': 0},
    ):
        from shared.rate_limit.check import check_or_raise

        start = time.perf_counter()
        decision = check_or_raise(ip='1.2.3.4', endpoint='/contact', country='CL')
        elapsed = time.perf_counter() - start

        assert decision.allowed is True
        assert elapsed < 0.2, f'Expected parallel execution < 200ms, got {elapsed*1000:.0f}ms'
```

### Test 2: short-circuit blacklist (AC-4)

```python
def test_check_or_raise_blacklist_raises_even_with_parallel(monkeypatch):
    """
    Given get_ip_rule retorna blacklist Y las otras 3 lookups exito,
    When check_or_raise corre,
    Then raise IPBlacklistedError ignorando los otros 3 resultados.
    """
    blacklist_rule = {
        'kind': 'ip_blacklist',
        'reason': 'spam',
        'expires_at': 9999999999,
    }
    with patch.multiple(
        'shared.rate_limit.check',
        get_ip_rule=lambda _: blacklist_rule,
        get_country_rule=lambda _: None,
        get_endpoint_rule=lambda _: {'limit': 100, 'window_seconds': 60},
        get_effective_count=lambda **_: 0.0,
    ):
        from shared.rate_limit.check import check_or_raise
        from shared.rate_limit.exceptions import IPBlacklistedError

        with pytest.raises(IPBlacklistedError) as exc:
            check_or_raise(ip='1.2.3.4', endpoint='/contact', country='CL')

        assert exc.value.code == 'IP_BLACKLISTED'
        assert exc.value.extra == {'ip': '1.2.3.4'}
```

### Test 3: country block (AC-4)

```python
def test_check_or_raise_country_block_raises(monkeypatch):
    """
    Given country_rule = block,
    When check_or_raise corre con ese country,
    Then raise CountryBlockedError.
    """
    with patch.multiple(
        'shared.rate_limit.check',
        get_ip_rule=lambda _: None,
        get_country_rule=lambda _: {'action': 'block', 'reason': 'sanctioned'},
        get_endpoint_rule=lambda _: {'limit': 100, 'window_seconds': 60},
        get_effective_count=lambda **_: 0.0,
    ):
        from shared.rate_limit.check import check_or_raise
        from shared.rate_limit.exceptions import CountryBlockedError

        with pytest.raises(CountryBlockedError) as exc:
            check_or_raise(ip='1.2.3.4', endpoint='/contact', country='XX')

        assert exc.value.code == 'COUNTRY_BLOCKED'
```

### Test 4: rate limit exceeded (AC-4)

```python
def test_check_or_raise_rate_limit_exceeded(monkeypatch):
    """
    Given endpoint_rule limit=5 y effective_count=10,
    When check_or_raise corre,
    Then raise RateLimitExceededError con limit + window correctos.
    """
    with patch.multiple(
        'shared.rate_limit.check',
        get_ip_rule=lambda _: None,
        get_country_rule=lambda _: None,
        get_endpoint_rule=lambda _: {'limit': 5, 'window_seconds': 60},
        get_effective_count=lambda **_: 10.0,
    ):
        from shared.rate_limit.check import check_or_raise
        from shared.rate_limit.exceptions import RateLimitExceededError

        with pytest.raises(RateLimitExceededError) as exc:
            check_or_raise(ip='1.2.3.4', endpoint='/contact', country='CL')

        assert exc.value.code == 'RATE_LIMIT_EXCEEDED'
        assert exc.value.extra['limit'] == 5
        assert exc.value.extra['window_seconds'] == 60
        assert exc.value.extra['effective_count'] == 10.0
```

## Verificacion

```bash
# 1. Unit tests del modulo paralelo (Red phase ANTES del refactor)
python devtools/run.py serverless tests --type=unit --shared

# 2. Coverage del check.py >= 80%
python devtools/run.py serverless tests --type=coverage --shared

# 3. Tests EXISTENTES de rate_limit siguen verdes (sin regresion)
python devtools/run.py serverless tests --type=unit --shared
```
