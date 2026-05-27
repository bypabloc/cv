"""
Given endpoint_rule limit=5 y effective_count=10,
When check_or_raise corre,
Then raise RateLimitExceededError con limit + window correctos.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.rate_limit.exceptions import RateLimitExceededError

pytestmark = pytest.mark.unit


def test_check_or_raise_parallel_rate_limit_exceeded() -> None:
    """effective >= limit raise RateLimitExceededError con extras correctos."""
    # Arrange
    with patch.multiple(
        'shared.rate_limit.check',
        get_ip_rule=lambda _ip: None,
        get_country_rule=lambda _country: None,
        get_endpoint_rule=lambda _endpoint: {
            'limit': 5,
            'window_seconds': 60,
        },
        get_effective_count=lambda **_kw: 10.0,
        increment_bucket=lambda **_: {'turnstile_tokens': 0},
    ):
        from shared.rate_limit.check import check_or_raise

        # Act + Assert
        with pytest.raises(RateLimitExceededError) as exc:
            check_or_raise(
                ip='1.2.3.4', endpoint='/contact', country='CL'
            )

    assert exc.value.code == 'RATE_LIMIT_EXCEEDED'
    assert exc.value.extra['limit'] == 5
    assert exc.value.extra['window_seconds'] == 60
    assert exc.value.extra['effective_count'] == 10.0
