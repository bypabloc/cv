"""
Given una funcion decorada con @cached y una tabla cache real,
When se la invoca dos veces con los mismos args,
Then la primera computa (MISS) y la segunda sirve del cache (HIT),
     de modo que la funcion subyacente corre una sola vez.
"""

from __future__ import annotations

import pytest
from shared.cache.decorator import cached

pytestmark = pytest.mark.integration


def test_cached_decorator_miss_computes_and_hits_e2e(cache_table: str) -> None:
    """@cached: MISS computa, la 2a llamada es HIT (compute corre 1 vez)."""
    # Arrange
    calls: list[int] = []

    @cached(ttl=300, namespace='it')
    def expensive(n: int) -> int:
        calls.append(n)
        return n * 10

    # Act
    first = expensive(4)
    second = expensive(4)

    # Assert
    assert first == 40
    assert second == 40
    assert calls == [4]
