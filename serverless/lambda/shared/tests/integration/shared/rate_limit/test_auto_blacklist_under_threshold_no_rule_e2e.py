"""
Given una IP que valida solo 2 tokens Turnstile (bajo el threshold de 3),
When check_or_raise corre 2 veces con turnstile_validated=True,
Then NO se crea ninguna rule ip_blacklist.
"""

from __future__ import annotations

import time

import pytest
from shared.dynamodb.models.rate_limit_rule import RateLimitRuleItem
from shared.rate_limit.check import check_or_raise

from ._fixtures import _add_endpoint_rule

pytestmark = pytest.mark.integration


def test_auto_blacklist_under_threshold_no_rule_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """2 tokens Turnstile (< threshold 3) no disparan el auto-blacklist."""
    # Arrange
    _add_endpoint_rule(endpoint='/contact', limit=100, window_seconds=60)
    now = int(time.time())

    # Act
    for _ in range(2):
        check_or_raise(
            ip='8.8.4.4',
            endpoint='/contact',
            turnstile_validated=True,
            now=now,
        )

    # Assert
    assert RateLimitRuleItem.get('ip#8.8.4.4', 'ip_blacklist') is None
