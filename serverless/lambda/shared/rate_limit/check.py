"""
API publica del rate-limit module: check_or_raise.

Flujo:
1. Check IP rule (whitelist/blacklist) -> skip o raise IPBlacklistedError
2. Check country rule -> raise CountryBlockedError si action=block
3. Get endpoint rule (limit + window_seconds)
4. Calcula effective_count sliding window weighted
5. Si effective >= limit -> raise RateLimitExceededError
6. Atomic INCREMENT bucket (count + turnstile_tokens si aplica)
7. Si turnstile_tokens >= threshold -> auto-blacklist
"""

from __future__ import annotations

import time

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


def check_or_raise(
    *,
    ip: str,
    endpoint: str,
    country: str | None = None,
    turnstile_validated: bool = False,
    now: int | None = None,
) -> Decision:
    """
    Verifica rate-limit + IP white/blacklist + country rules.

    Args:
        ip: IP del cliente (CF-Connecting-IP).
        endpoint: path del endpoint (ej: '/contact').
        country: country code (ISO 3166-1 alpha-2) o None.
        turnstile_validated: si la request paso Turnstile siteverify ya.
        now: timestamp override (tests).

    Returns:
        Decision (cuando allowed).

    Raises:
        IPBlacklistedError: IP en blacklist.
        CountryBlockedError: country rule action=block.
        RateLimitExceededError: sliding window weighted >= limit.
    """
    current_time = now if now is not None else int(time.time())

    # 1. IP rule (whitelist/blacklist)
    ip_rule = get_ip_rule(ip)
    if ip_rule is not None:
        kind = ip_rule.get('kind', '')
        if kind == 'ip_whitelist':
            return Decision(
                allowed=True, reason='ip_whitelist', status_code=200,
            )
        if kind == 'ip_blacklist':
            expires = ip_rule.get('expires_at', 0)
            retry_after = max(expires - current_time, 60) if expires else AUTO_BLACKLIST_DURATION_SECONDS
            raise IPBlacklistedError(
                ip_rule.get('reason', 'IP blacklisted'),
                code='IP_BLACKLISTED',
                retry_after_seconds=int(retry_after),
                extra={'ip': ip},
            )

    # 2. Country rule
    if country:
        country_rule = get_country_rule(country)
        if (
            country_rule is not None
            and country_rule.get('action') == 'block'
        ):
            raise CountryBlockedError(
                country_rule.get('reason', f'Country {country} blocked'),
                code='COUNTRY_BLOCKED',
                extra={'country': country},
            )

    # 3. Endpoint rule
    endpoint_rule = get_endpoint_rule(endpoint)
    if endpoint_rule is None:
        limit = DEFAULT_LIMIT
        window_seconds = DEFAULT_WINDOW_SECONDS
    else:
        limit = endpoint_rule.get('limit', DEFAULT_LIMIT)
        window_seconds = endpoint_rule.get(
            'window_seconds', DEFAULT_WINDOW_SECONDS
        )

    # 4. Effective count + check
    effective = get_effective_count(
        ip=ip,
        endpoint=endpoint,
        window_seconds=window_seconds,
        now=current_time,
    )
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

    # 5. Atomic INCREMENT
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
