"""
Given una rule ip_blacklist para una IP,
When check_or_raise corre para esa IP,
Then levanta IPBlacklistedError antes de evaluar el rate-limit.
"""

from __future__ import annotations

import time

import pytest
from shared.rate_limit.check import check_or_raise
from shared.rate_limit.exceptions import IPBlacklistedError

from ._fixtures import _add_ip_rule

pytestmark = pytest.mark.integration


def test_check_ip_blacklist_raises_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """Una IP blacklisteada levanta IPBlacklistedError."""
    # Arrange
    _add_ip_rule(ip='6.6.6.6', kind='ip_blacklist', reason='abuse')
    now = int(time.time())

    # Act / Assert
    with pytest.raises(IPBlacklistedError):
        check_or_raise(ip='6.6.6.6', endpoint='/contact', now=now)
