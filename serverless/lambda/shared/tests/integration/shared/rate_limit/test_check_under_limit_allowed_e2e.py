"""
Given una rule de endpoint con limit=3 y las 3 tablas de rate-limit,
When check_or_raise se invoca 3 veces bajo el limite,
Then las 3 devuelven una Decision allowed (flujo completo sin raise).
"""

from __future__ import annotations

import time

import pytest
from shared.rate_limit.check import check_or_raise

from ._fixtures import _add_endpoint_rule

pytestmark = pytest.mark.integration


def test_check_under_limit_allowed_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """3 requests bajo limit=3 -> 3 Decision allowed."""
    # Arrange
    _add_endpoint_rule(endpoint='/contact', limit=3, window_seconds=60)
    now = int(time.time())

    # Act
    decisions = [
        check_or_raise(ip='1.2.3.4', endpoint='/contact', now=now)
        for _ in range(3)
    ]

    # Assert
    assert [d['allowed'] for d in decisions] == [True, True, True]
