"""
Rate-limit rules lookup.

Tabla `rate_limit_rules` con schema:
    PK: rule_key (string)        # ej: 'endpoint#/contact', 'ip#1.2.3.4', 'country#CN'
    SK: kind (string)             # 'endpoint' | 'ip_whitelist' | 'ip_blacklist' | 'country'
    limit: number                 # max requests por window
    window_seconds: number        # ventana en segundos
    action: string                # 'throttle' | 'block'
    expires_at: number (TTL)      # para auto-blacklist con expiration
    reason: string                # texto humano
    metadata: map                 # context opcional

Decision: las rules cambian raramente, son read-heavy. Cache con
`@cached(ttl=60, stale_for=300)` para reducir reads DynamoDB.

La persistencia la hace el ORM (`shared.dynamodb.RateLimitRuleItem`):
`get()` para el lookup; la conversion `Decimal -> int` la hace el ORM.
Las funciones publicas devuelven un `dict` (no el modelo) porque el
resultado lo cachea `@cached`, que serializa a JSON — un modelo Pydantic
no es JSON-serializable. El `dict` conserva la API `.get(...)` que usa
`check.py`.
"""

from __future__ import annotations

import time
from typing import Any, TypedDict

from shared.cache.decorator import cached
from shared.dynamodb.models.rate_limit_rule import RateLimitRuleItem


class RateLimitRule(TypedDict, total=False):
    """Shape de una rule (dict devuelto por los lookups).

    Es el `model_dump(exclude_none=True)` de un `RateLimitRuleItem`.
    Se mantiene como TypedDict para tipar el retorno cacheado.
    """

    rule_key: str
    kind: str
    limit: int
    window_seconds: int
    action: str
    expires_at: int
    reason: str
    metadata: dict[str, Any]


def _to_rule_dict(item: RateLimitRuleItem | None) -> RateLimitRule | None:
    """Convierte el modelo del ORM a un dict JSON-serializable (cacheable)."""
    if item is None:
        return None
    return item.model_dump(exclude_none=True)  # type: ignore[return-value]


@cached(
    ttl=60, stale_for=300, namespace='rate_limit', tags=['rate-limit-rules']
)
def get_endpoint_rule(endpoint: str) -> RateLimitRule | None:
    """
    Lookup de rule por endpoint (ej: '/contact', '/track').

    Returns:
        Rule dict o None si no existe.
    """
    return _to_rule_dict(
        RateLimitRuleItem.get(f'endpoint#{endpoint}', 'endpoint')
    )


@cached(
    ttl=60, stale_for=300, namespace='rate_limit', tags=['rate-limit-rules']
)
def get_ip_rule(ip: str) -> RateLimitRule | None:
    """
    Lookup de rule por IP (whitelist o blacklist).

    Returns:
        Rule con kind in {ip_whitelist, ip_blacklist} o None.
    """
    # Buscar primero whitelist (priority alta)
    for kind in ('ip_whitelist', 'ip_blacklist'):
        rule = RateLimitRuleItem.get(f'ip#{ip}', kind)
        if rule is None:
            continue
        # Si tiene expires_at y ya expiro, ignorar (TTL service la borrara).
        expires = rule.expires_at or 0
        if expires and expires < int(time.time()):
            continue
        return _to_rule_dict(rule)
    return None


@cached(
    ttl=60, stale_for=300, namespace='rate_limit', tags=['rate-limit-rules']
)
def get_country_rule(country: str) -> RateLimitRule | None:
    """
    Lookup de rule por country code.

    Returns:
        Rule con kind=country o None.
    """
    return _to_rule_dict(RateLimitRuleItem.get(f'country#{country}', 'country'))
