"""
Given una rule ip_whitelist para una IP y un limit bajo,
When check_or_raise corre para esa IP por encima del limit,
Then siempre devuelve allowed con reason 'ip_whitelist' (skip del limite).
"""

from __future__ import annotations

import time

import pytest
from shared.rate_limit.check import check_or_raise

from ._fixtures import _add_endpoint_rule, _add_ip_rule

pytestmark = pytest.mark.integration


def test_check_ip_whitelist_skips_limit_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """Una IP whitelisteada nunca pega contra el rate-limit."""
    # Arrange
    _add_endpoint_rule(endpoint='/contact', limit=1, window_seconds=60)
    _add_ip_rule(ip='5.5.5.5', kind='ip_whitelist')
    now = int(time.time())

    # Act
    decisions = [
        check_or_raise(ip='5.5.5.5', endpoint='/contact', now=now)
        for _ in range(5)
    ]

    # Assert
    assert all(d['reason'] == 'ip_whitelist' for d in decisions)
