"""
API publica del rate-limit module: check_or_raise (PARALELO).

Las 4 lookups DDB (ip_rule, country_rule, endpoint_rule, effective_count)
se lanzan en paralelo con ThreadPoolExecutor(max_workers=4). La logica
condicional (short-circuit ip blacklist -> country block -> endpoint limit)
se aplica DESPUES con los 4 resultados ya disponibles.

Trade-off: si la IP esta blacklisteada, gastamos 3 DDB reads "inutiles"
(~$0.0000001 cada uno — irrelevante). Beneficio: latencia = max(4) en vez
de sum(4), ahorra ~300-500ms en cold path y ~100-200ms en warm.

Flujo logico (preservado del orden secuencial anterior):
1. Lanza las 4 lookups en paralelo (sentinel _NOT_REQUESTED para country=None)
2. Espera los 4 resultados (block hasta el mas lento)
3. Aplica logica condicional sobre los 4 resultados:
   - IP whitelist -> Decision allowed (skip resto)
   - IP blacklist -> raise IPBlacklistedError
   - Country block -> raise CountryBlockedError
   - Effective >= limit -> raise RateLimitExceededError
4. Atomic INCREMENT bucket (con window_seconds REAL del endpoint_rule)
5. Si turnstile_tokens >= threshold -> auto-blacklist

NOTA: get_effective_count se lanza con DEFAULT_WINDOW_SECONDS (60) en la
paralela porque endpoint_rule aun no esta disponible. Si en el futuro un
endpoint usa window distinto (ningun rule actual lo hace), el effective
count se mide en una ventana de 60s — es seguro: el increment_bucket
posterior usa el window REAL para construir el bucket_key correcto.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from shared.rate_limit.auto_blacklist import (
    AUTO_BLACKLIST_DURATION_SECONDS,
    create_blacklist_rule,
    should_auto_blacklist,
)
from shared.rate_limit.buckets import get_effective_count, increment_bucket
from shared.rate_limit.decisions import Decision
from shared.rate_limit.exceptions import (
    CountryBlockedError,
    IPBlacklistedError,
    RateLimitExceededError,
)
from shared.rate_limit.rules import (
    get_country_rule,
    get_endpoint_rule,
    get_ip_rule,
)

# Defaults si no hay rule en DB para el endpoint
DEFAULT_LIMIT = 10
DEFAULT_WINDOW_SECONDS = 60

# Sentinel para indicar que la lookup country no se ejecuto (country=None).
# Distinto de None (resultado real "sin rule") para que la logica condicional
# distinga 'no preguntamos' de 'preguntamos y no hay rule'.
_NOT_REQUESTED: Any = object()


def check_or_raise(
    *,
    ip: str,
    endpoint: str,
    country: str | None = None,
    turnstile_validated: bool = False,
    brought_turnstile_token: bool = False,
    now: int | None = None,
) -> Decision:
    """
    Verifica rate-limit + IP white/blacklist + country rules (PARALELO).

    Args:
        ip: IP del cliente (CF-Connecting-IP).
        endpoint: path del endpoint (ej: '/contact').
        country: country code (ISO 3166-1 alpha-2) o None.
        turnstile_validated: si la request paso Turnstile siteverify ya.
            Controla SOLO el limite del rate-limit; NO alimenta la
            auto-blacklist (los verify-*/mfa/session lo pasan True sin traer
            un token real del usuario).
        brought_turnstile_token: True solo si el request trajo un token
            Turnstile REAL del usuario (login.start/register.start). Es el
            unico que alimenta el counter de auto-blacklist (bot detection).
            Sin esta separacion, un humano que reintenta un login/magic-link
            3 veces en 60s se auto-blacklistea 24h.
        now: timestamp override (tests).

    Returns:
        Decision (cuando allowed).

    Raises:
        IPBlacklistedError: IP en blacklist.
        CountryBlockedError: country rule action=block.
        RateLimitExceededError: sliding window weighted >= limit.
    """
    current_time = now if now is not None else int(time.time())

    # --- Lanza las 4 lookups en paralelo ---
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_ip = executor.submit(get_ip_rule, ip)
        future_country = (
            executor.submit(get_country_rule, country) if country else None
        )
        future_endpoint = executor.submit(get_endpoint_rule, endpoint)
        # NOTA: usa DEFAULT_WINDOW_SECONDS para el effective_count porque
        # endpoint_rule aun no esta disponible. Si el rule tiene window
        # distinto, el effective_count se mide en una ventana de 60s — es
        # seguro: increment_bucket usa el window REAL para el bucket_key.
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

    # 1. IP rule (whitelist/blacklist)
    if ip_rule is not None:
        kind = ip_rule.get('kind', '')
        if kind == 'ip_whitelist':
            return Decision(
                allowed=True, reason='ip_whitelist', status_code=200,
            )
        if kind == 'ip_blacklist':
            expires = ip_rule.get('expires_at', 0)
            # Respeta expires_at aun cuando la rule viene del cache:
            # get_ip_rule esta @cached(stale_for=300), asi que puede servir
            # una blacklist YA VENCIDA hasta 300s pasado su expiry. Si ya
            # expiro, NO bloquear (caer al resto del rate-limit normal); el
            # TTL service de DynamoDB borrara la rule.
            if not expires or expires >= current_time:
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
    if (
        country
        and country_rule is not _NOT_REQUESTED
        and country_rule is not None
        and country_rule.get('action') == 'block'
    ):
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
        window_seconds = endpoint_rule.get(
            'window_seconds', DEFAULT_WINDOW_SECONDS
        )

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

    # 5. Atomic INCREMENT (con el window_seconds REAL del rule). El counter
    #    turnstile_tokens (auto-blacklist) solo sube si el request adjunto un
    #    CAPTCHA real del usuario (login.start/register.start), NO si
    #    turnstile_validated=True por bypass de limite (verify-*/mfa/session).
    real_captcha = brought_turnstile_token
    bucket = increment_bucket(
        ip=ip,
        endpoint=endpoint,
        window_seconds=window_seconds,
        brought_turnstile_token=real_captcha,
        now=current_time,
    )

    # 6. Auto-blacklist check: solo cuando el request adjunto un CAPTCHA real.
    if real_captcha and should_auto_blacklist(bucket['turnstile_tokens']):
        create_blacklist_rule(ip)

    return Decision(allowed=True, reason='allowed', status_code=200)
