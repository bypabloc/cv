"""
Given multiples invocadores concurrentes incrementando el mismo bucket,
When 20 increment_bucket corren via ThreadPoolExecutor,
Then el ADD atomico de DynamoDB no pierde updates: el counter final es 20.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from shared.rate_limit.buckets import get_effective_count, increment_bucket

pytestmark = pytest.mark.integration


def test_buckets_concurrent_increment_no_lost_updates_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """20 increments concurrentes -> counter final exacto 20."""
    # Arrange
    now = 1_715_000_000

    def _inc(_: int) -> None:
        increment_bucket(
            ip='3.3.3.3',
            endpoint='/track',
            window_seconds=60,
            now=now,
        )

    # Act
    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(_inc, range(20)))
    effective = get_effective_count(
        ip='3.3.3.3',
        endpoint='/track',
        window_seconds=60,
        now=now,
    )

    # Assert
    assert effective == 20.0
