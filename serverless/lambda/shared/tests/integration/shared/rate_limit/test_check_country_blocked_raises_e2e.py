"""
Given una rule de country con action='block',
When check_or_raise corre con ese country code,
Then levanta CountryBlockedError.
"""

from __future__ import annotations

import time

import pytest
from shared.rate_limit.check import check_or_raise
from shared.rate_limit.exceptions import CountryBlockedError

from ._fixtures import _add_country_rule

pytestmark = pytest.mark.integration


def test_check_country_blocked_raises_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """Un country bloqueado levanta CountryBlockedError."""
    # Arrange
    _add_country_rule(country='CN', action='block')
    now = int(time.time())

    # Act / Assert
    with pytest.raises(CountryBlockedError):
        check_or_raise(
            ip='7.7.7.7',
            endpoint='/contact',
            country='CN',
            now=now,
        )
