"""
Auto-blacklist por bot detection con Turnstile solver.

Heuristic: si una IP genera 3+ tokens Turnstile validos en 60 segundos,
es probable que sea un bot usando un Turnstile solver (servicio de pago
que resuelve CAPTCHAs por API). Bloqueamos esa IP por 24h.

Implementacion:
- Cada vez que increment_bucket() pasa turnstile_validated=True, incrementa
  el counter turnstile_tokens del bucket actual.
- Si turnstile_tokens >= 3 en una ventana de 60s, crear rule
  rule_key='ip#<addr>' kind='ip_blacklist' con TTL = now + 86400.

La rule blacklist se respeta en la siguiente request (lookup en rules.get_ip_rule).

La persistencia la hace el ORM (`shared.dynamodb.RateLimitRuleItem`):
`save()` para crear la rule, reusando el resource boto3 singleton.
"""

from __future__ import annotations

import time

from shared.dynamodb.models.rate_limit_rule import RateLimitRuleItem

# Threshold: 3+ tokens validos en 60s = sospechoso
AUTO_BLACKLIST_THRESHOLD = 3
AUTO_BLACKLIST_WINDOW_SECONDS = 60
AUTO_BLACKLIST_DURATION_SECONDS = 86400  # 24h


def should_auto_blacklist(turnstile_tokens_count: int) -> bool:
    """
    True si el counter de turnstile_tokens cruzo el threshold.

    Args:
        turnstile_tokens_count: count actual de tokens validos en la ventana.

    Returns:
        True si turnstile_tokens >= threshold.
    """
    return turnstile_tokens_count >= AUTO_BLACKLIST_THRESHOLD


def create_blacklist_rule(
    ip: str,
    *,
    duration_seconds: int = AUTO_BLACKLIST_DURATION_SECONDS,
    reason: str = 'auto-blacklist: 3+ turnstile tokens in 60s',
) -> None:
    """
    Crea una rule ip_blacklist con TTL.

    Idempotente: si ya existe, se actualiza con el nuevo expires_at.

    Args:
        ip: IP a bloquear.
        duration_seconds: cuanto durar el bloqueo (default 24h).
        reason: texto humano para auditoria.
    """
    expires_at = int(time.time()) + duration_seconds

    RateLimitRuleItem(
        rule_key=f'ip#{ip}',
        kind='ip_blacklist',
        action='block',
        expires_at=expires_at,
        reason=reason,
        metadata={
            'auto_created': True,
            'threshold': AUTO_BLACKLIST_THRESHOLD,
            'window_seconds': AUTO_BLACKLIST_WINDOW_SECONDS,
        },
    ).save()

    # Invalida el cache de rules: get_ip_rule esta @cached(ttl=60,
    # stale_for=300) y pudo cachear un None (IP sin rule) en las requests
    # previas del bot. Sin esta invalidacion la blacklist recien creada no
    # surte efecto hasta 60-360s despues y el bot sigue pasando.
    # Best-effort: un fallo de invalidacion no debe abortar el bloqueo.
    try:
        from shared.cache.client import DynamoDBCache

        DynamoDBCache().invalidate(tag='rate-limit-rules')
    except Exception:
        from shared.observability.logger import logger

        logger.warning('rate-limit cache invalidation failed after blacklist')
