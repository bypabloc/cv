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
"""

from __future__ import annotations

import os
import time
from typing import Any, TypedDict

import boto3

from common.cache.decorator import cached


class RateLimitRule(TypedDict, total=False):
    """Shape de una rule en DynamoDB."""

    rule_key: str
    kind: str
    limit: int
    window_seconds: int
    action: str
    expires_at: int
    reason: str
    metadata: dict[str, Any]


def _rules_table() -> Any:
    """Lazy boto3 Resource para rate_limit_rules table."""
    region = os.environ.get('AWS_REGION', 'us-east-1')
    table_name = os.environ.get(
        'RATE_LIMIT_RULES_TABLE_NAME', 'portfolio-rate-limit-rules-dev'
    )
    return boto3.resource('dynamodb', region_name=region).Table(table_name)


@cached(ttl=60, stale_for=300, namespace='rate_limit', tags=['rate-limit-rules'])
def get_endpoint_rule(endpoint: str) -> RateLimitRule | None:
    """
    Lookup de rule por endpoint (ej: '/contact', '/track').

    Returns:
        Rule dict o None si no existe.
    """
    table = _rules_table()
    result = table.get_item(Key={'rule_key': f'endpoint#{endpoint}', 'kind': 'endpoint'})
    item = result.get('Item')
    if item is None:
        return None
    return _normalize_rule(item)


@cached(ttl=60, stale_for=300, namespace='rate_limit', tags=['rate-limit-rules'])
def get_ip_rule(ip: str) -> RateLimitRule | None:
    """
    Lookup de rule por IP (whitelist o blacklist).

    Returns:
        Rule con kind in {ip_whitelist, ip_blacklist} o None.
    """
    table = _rules_table()
    # Buscar primero whitelist (priority alta)
    for kind in ('ip_whitelist', 'ip_blacklist'):
        result = table.get_item(Key={'rule_key': f'ip#{ip}', 'kind': kind})
        item = result.get('Item')
        if item is None:
            continue
        normalized = _normalize_rule(item)
        # Si tiene expires_at y ya expiro, ignorar (TTL service la borrara)
        expires = normalized.get('expires_at', 0)
        if expires and expires < int(time.time()):
            continue
        return normalized
    return None


@cached(ttl=60, stale_for=300, namespace='rate_limit', tags=['rate-limit-rules'])
def get_country_rule(country: str) -> RateLimitRule | None:
    """
    Lookup de rule por country code.

    Returns:
        Rule con kind=country o None.
    """
    table = _rules_table()
    result = table.get_item(Key={'rule_key': f'country#{country}', 'kind': 'country'})
    item = result.get('Item')
    if item is None:
        return None
    return _normalize_rule(item)


def _normalize_rule(item: dict[str, Any]) -> RateLimitRule:
    """Convierte Decimal de DynamoDB a int para enteros."""
    normalized: RateLimitRule = {
        'rule_key': item['rule_key'],
        'kind': item['kind'],
    }
    if 'limit' in item:
        normalized['limit'] = int(item['limit'])
    if 'window_seconds' in item:
        normalized['window_seconds'] = int(item['window_seconds'])
    if 'action' in item:
        normalized['action'] = item['action']
    if 'expires_at' in item:
        normalized['expires_at'] = int(item['expires_at'])
    if 'reason' in item:
        normalized['reason'] = item['reason']
    if 'metadata' in item:
        normalized['metadata'] = item['metadata']
    return normalized
