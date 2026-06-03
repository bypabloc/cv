"""
Given una IP que adjunta 10 CAPTCHAs Turnstile reales en la misma ventana
de 60s, When check_or_raise corre la 10a vez con brought_turnstile_token=True,
Then el auto-blacklist crea una rule ip_blacklist con TTL en DynamoDB.
"""

from __future__ import annotations

import time

import pytest
from shared.dynamodb.models.rate_limit_rule import RateLimitRuleItem
from shared.rate_limit.auto_blacklist import AUTO_BLACKLIST_THRESHOLD
from shared.rate_limit.check import check_or_raise

from ._fixtures import _add_endpoint_rule

pytestmark = pytest.mark.integration


def test_auto_blacklist_threshold_creates_rule_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """AUTO_BLACKLIST_THRESHOLD CAPTCHAs reales en 60s -> rule creada."""
    # Arrange: limit alto para que el rate-limit no levante antes.
    _add_endpoint_rule(endpoint='/contact', limit=1000, window_seconds=60)
    now = int(time.time())

    # Act: THRESHOLD requests con CAPTCHA real adjuntado desde la misma IP.
    for _ in range(AUTO_BLACKLIST_THRESHOLD):
        check_or_raise(
            ip='8.8.8.8',
            endpoint='/contact',
            brought_turnstile_token=True,
            now=now,
        )

    # Assert: el auto-blacklist creo la rule ip_blacklist.
    rule = RateLimitRuleItem.get('ip#8.8.8.8', 'ip_blacklist')
    assert rule is not None
    assert rule.action == 'block'
    assert rule.expires_at is not None
