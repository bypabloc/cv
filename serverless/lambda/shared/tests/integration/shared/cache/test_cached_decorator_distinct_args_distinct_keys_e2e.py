"""
Given una funcion @cached invocada con args distintos,
When se la llama con n=1 y n=2,
Then cada conjunto de args genera su propio cache key y se computa
     una vez por cada uno (no hay colision de keys).
"""

from __future__ import annotations

import pytest
from shared.cache.decorator import cached

pytestmark = pytest.mark.integration


def test_cached_decorator_distinct_args_distinct_keys_e2e(
    cache_table: str,
) -> None:
    """@cached: args distintos -> keys distintos -> compute por cada arg."""
    # Arrange
    calls: list[int] = []

    @cached(ttl=300, namespace='it')
    def squared(n: int) -> int:
        calls.append(n)
        return n * n

    # Act
    results = [squared(1), squared(2), squared(1), squared(2)]

    # Assert
    assert results == [1, 4, 1, 4]
    assert sorted(calls) == [1, 2]
