"""Builders compartidos por los integration tests de rate_limit.

Prefijo `_` para que pytest no recolecte este modulo como tests. Crean
rules directamente en la tabla DynamoDB via el ORM e invalidan el cache
de rules para que el proximo lookup las vea.
"""

from __future__ import annotations

from shared.dynamodb.models.rate_limit_rule import RateLimitRuleItem


def _invalidate_rules_cache() -> None:
    """Tag-invalida 'rate-limit-rules' en la tabla cache.

    Las funciones `get_*_rule` estan decoradas con
    `@cached(tags=['rate-limit-rules'])`; sin invalidar, un lookup
    posterior a la creacion de una rule devolveria el valor cacheado.
    """
    from shared.cache.client import DynamoDBCache

    DynamoDBCache().invalidate(tag='rate-limit-rules')


def _add_endpoint_rule(
    *, endpoint: str, limit: int, window_seconds: int
) -> None:
    """Crea una rule de endpoint y limpia el cache de rules."""
    RateLimitRuleItem(
        rule_key=f'endpoint#{endpoint}',
        kind='endpoint',
        limit=limit,
        window_seconds=window_seconds,
        action='throttle',
    ).save()
    _invalidate_rules_cache()


def _add_ip_rule(*, ip: str, kind: str, reason: str = '') -> None:
    """Crea una rule de IP whitelist/blacklist y limpia el cache."""
    RateLimitRuleItem(
        rule_key=f'ip#{ip}',
        kind=kind,
        action='block' if kind == 'ip_blacklist' else 'allow',
        reason=reason or kind,
    ).save()
    _invalidate_rules_cache()


def _add_country_rule(*, country: str, action: str = 'block') -> None:
    """Crea una rule de country y limpia el cache."""
    RateLimitRuleItem(
        rule_key=f'country#{country}',
        kind='country',
        action=action,
        reason=f'{country} {action}',
    ).save()
    _invalidate_rules_cache()
