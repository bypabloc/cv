"""
Given un bucket previo con conteo y una ventana actual con conteo propio,
When get_effective_count corre a mitad de la ventana actual,
Then el effective count interpola: current + previous * (1 - elapsed_fraction).
"""

from __future__ import annotations

import pytest
from shared.rate_limit.buckets import get_effective_count, increment_bucket

pytestmark = pytest.mark.integration


def test_buckets_window_transition_interpolation_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """A mitad de la ventana, el bucket previo pesa 0.5 en el effective."""
    # Arrange: window=60. previous_start alineado a multiplo de 60
    # (1_715_000_040 % 60 == 0) para que _window_start no lo redondee.
    window = 60
    previous_start = 1_715_000_040
    current_start = previous_start + window
    # 4 hits en la ventana previa.
    for _ in range(4):
        increment_bucket(
            ip='4.4.4.4',
            endpoint='/track',
            window_seconds=window,
            now=previous_start + 1,
        )
    # 2 hits en la ventana actual.
    for _ in range(2):
        increment_bucket(
            ip='4.4.4.4',
            endpoint='/track',
            window_seconds=window,
            now=current_start + 1,
        )

    # Act: now a mitad de la ventana actual (elapsed_fraction = 0.5).
    effective = get_effective_count(
        ip='4.4.4.4',
        endpoint='/track',
        window_seconds=window,
        now=current_start + 30,
    )

    # Assert: 2 (current) + 4 * (1 - 0.5) = 4.0
    assert effective == 4.0
