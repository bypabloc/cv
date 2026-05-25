"""
Given una rule de endpoint con limit=2,
When check_or_raise se invoca una 3a vez en la misma ventana,
Then levanta RateLimitExceededError (sliding window weighted >= limit).
"""

from __future__ import annotations

import time

import pytest
from shared.rate_limit.check import check_or_raise
from shared.rate_limit.exceptions import RateLimitExceededError

from ._fixtures import _add_endpoint_rule

pytestmark = pytest.mark.integration


def test_check_over_limit_raises_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """La 3a request con limit=2 levanta RateLimitExceededError."""
    # Arrange
    _add_endpoint_rule(endpoint='/contact', limit=2, window_seconds=60)
    now = int(time.time())
    check_or_raise(ip='9.9.9.9', endpoint='/contact', now=now)
    check_or_raise(ip='9.9.9.9', endpoint='/contact', now=now)

    # Act / Assert
    with pytest.raises(RateLimitExceededError):
        check_or_raise(ip='9.9.9.9', endpoint='/contact', now=now)
