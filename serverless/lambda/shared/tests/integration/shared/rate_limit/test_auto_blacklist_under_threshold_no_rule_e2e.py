"""
Given una IP que adjunta CAPTCHAs reales bajo el threshold (THRESHOLD - 1),
When check_or_raise corre esas veces con brought_turnstile_token=True,
Then NO se crea ninguna rule ip_blacklist.
"""

from __future__ import annotations

import time

import pytest
from shared.dynamodb.models.rate_limit_rule import RateLimitRuleItem
from shared.rate_limit.auto_blacklist import AUTO_BLACKLIST_THRESHOLD
from shared.rate_limit.check import check_or_raise

from ._fixtures import _add_endpoint_rule

pytestmark = pytest.mark.integration


def test_auto_blacklist_under_threshold_no_rule_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """THRESHOLD-1 CAPTCHAs reales (< threshold) no disparan el auto-blacklist."""
    # Arrange
    _add_endpoint_rule(endpoint='/contact', limit=1000, window_seconds=60)
    now = int(time.time())

    # Act
    for _ in range(AUTO_BLACKLIST_THRESHOLD - 1):
        check_or_raise(
            ip='8.8.4.4',
            endpoint='/contact',
            brought_turnstile_token=True,
            now=now,
        )

    # Assert
    assert RateLimitRuleItem.get('ip#8.8.4.4', 'ip_blacklist') is None
