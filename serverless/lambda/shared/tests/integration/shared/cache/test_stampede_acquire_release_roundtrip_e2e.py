"""
Given una tabla cache real,
When se adquiere el lock distribuido y luego se libera con el holder
     correcto,
Then acquire_lock devuelve un holder_id y release_lock devuelve True.
"""

from __future__ import annotations

import pytest
from shared.cache import DynamoDBCache
from shared.cache.stampede import acquire_lock, release_lock

pytestmark = pytest.mark.integration


def test_stampede_acquire_release_roundtrip_e2e(cache_table: str) -> None:
    """acquire_lock crea el lock; release_lock con el holder lo borra."""
    # Arrange
    table = DynamoDBCache().table

    # Act
    holder = acquire_lock(table, 'job:1', ttl_seconds=15)
    released = release_lock(table, 'job:1', holder)

    # Assert
    assert holder is not None
    assert released is True
