"""
Given las 4 lookups DDB demoran 100ms cada una con mock dirigido,
When check_or_raise corre,
Then total duration es < 200ms (max + overhead), nunca > sum(4)~400ms.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_check_or_raise_parallel_total_under_max_when_all_slow() -> None:
    """Las 4 DDB lookups corren en paralelo: total = max(4) + overhead."""
    # Arrange: cada lookup demora 100ms
    def slow_ip(_ip: str) -> None:
        time.sleep(0.1)
        return None

    def slow_country(_country: str) -> None:
        time.sleep(0.1)
        return None

    def slow_endpoint(_endpoint: str) -> dict:
        time.sleep(0.1)
        return {'limit': 100, 'window_seconds': 60}

    def slow_effective(**_kw: object) -> float:
        time.sleep(0.1)
        return 0.0

    with patch.multiple(
        'shared.rate_limit.check',
        get_ip_rule=slow_ip,
        get_country_rule=slow_country,
        get_endpoint_rule=slow_endpoint,
        get_effective_count=slow_effective,
        increment_bucket=lambda **_: {'turnstile_tokens': 0},
    ):
        from shared.rate_limit.check import check_or_raise

        # Act
        start = time.perf_counter()
        decision = check_or_raise(
            ip='1.2.3.4', endpoint='/contact', country='CL'
        )
        elapsed = time.perf_counter() - start

    # Assert: max(4x100ms) + overhead, NO sum(4x100ms = 400ms)
    assert decision['allowed'] is True
    assert elapsed < 0.2, (
        f'Expected parallel execution < 200ms, got {elapsed * 1000:.0f}ms'
    )
