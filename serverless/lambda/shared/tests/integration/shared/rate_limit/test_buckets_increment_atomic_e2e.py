"""
Given la tabla de buckets DynamoDB real,
When increment_bucket se llama 5 veces para el mismo (ip, endpoint, window),
Then el counter atomico ADD acumula a 5 y get_effective_count lo refleja.
"""

from __future__ import annotations

import pytest
from shared.rate_limit.buckets import get_effective_count, increment_bucket

pytestmark = pytest.mark.integration


def test_buckets_increment_atomic_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """5 increment_bucket en la misma ventana acumulan count=5."""
    # Arrange
    now = 1_715_000_000  # multiplo arbitrario, alineado a la ventana

    # Act
    last = {}
    for _ in range(5):
        last = increment_bucket(
            ip='2.2.2.2',
            endpoint='/track',
            window_seconds=60,
            now=now,
        )
    effective = get_effective_count(
        ip='2.2.2.2',
        endpoint='/track',
        window_seconds=60,
        now=now,
    )

    # Assert
    assert last['count'] == 5
    assert effective == 5.0
