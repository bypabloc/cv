"""
Given country_rule = block y ip_rule = None,
When check_or_raise corre con ese country,
Then raise CountryBlockedError.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.rate_limit.exceptions import CountryBlockedError

pytestmark = pytest.mark.unit


def test_check_or_raise_parallel_country_block_raises() -> None:
    """Country rule = block raise CountryBlockedError tras evaluar los 4."""
    # Arrange
    with patch.multiple(
        'shared.rate_limit.check',
        get_ip_rule=lambda _ip: None,
        get_country_rule=lambda _country: {
            'action': 'block',
            'reason': 'sanctioned',
        },
        get_endpoint_rule=lambda _endpoint: {
            'limit': 100,
            'window_seconds': 60,
        },
        get_effective_count=lambda **_kw: 0.0,
        increment_bucket=lambda **_: {'turnstile_tokens': 0},
    ):
        from shared.rate_limit.check import check_or_raise

        # Act + Assert
        with pytest.raises(CountryBlockedError) as exc:
            check_or_raise(
                ip='1.2.3.4', endpoint='/contact', country='XX'
            )

    assert exc.value.code == 'COUNTRY_BLOCKED'
