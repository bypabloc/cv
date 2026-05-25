"""
Given una @cached con el entry EXPIRED y el lock distribuido ya tomado
     por otro holder,
When se invoca la funcion decorada,
Then tras el busy-wait el lock sigue ocupado y la funcion recomputa
     sin lock (preferir servir resultado antes que fallar).
"""

from __future__ import annotations

import pytest
from shared.cache import DynamoDBCache, cached
from shared.cache.stampede import acquire_lock

pytestmark = pytest.mark.integration


def test_cached_decorator_lock_busy_recomputes_e2e(cache_table: str) -> None:
    """@cached con lock ocupado y entry EXPIRED -> recompute sin lock."""
    # Arrange
    cache = DynamoDBCache()
    calls: list[int] = []

    @cached(ttl=300, namespace='it', busy_wait_ms=1)
    def build() -> str:
        calls.append(1)
        return 'recomputed'

    # El key que el decorator usa para esta funcion (mismo algoritmo).
    from shared.cache.decorator import _hash_call

    key = f'it:build:{_hash_call("build", (), {})}'
    # Entry EXPIRED: fuerza la rama de lock.
    cache.set(key, 'old', ttl=-10)
    # Lock tomado por OTRO holder: acquire_lock del decorator dara None.
    holder = acquire_lock(cache.table, key, ttl_seconds=300)

    # Act
    result = build()

    # Assert
    assert holder is not None
    assert result == 'recomputed'
    assert calls == [1]
