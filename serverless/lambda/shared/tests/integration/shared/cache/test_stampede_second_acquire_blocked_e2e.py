"""
Given un lock distribuido ya adquirido por un holder,
When un segundo invocador intenta acquire_lock sobre el mismo key,
Then la ConditionExpression falla y el segundo recibe None (lock ocupado).
"""

from __future__ import annotations

import pytest
from shared.cache.client import DynamoDBCache
from shared.cache.stampede import acquire_lock

pytestmark = pytest.mark.integration


def test_stampede_second_acquire_blocked_e2e(cache_table: str) -> None:
    """El 2o acquire_lock sobre un lock vigente devuelve None."""
    # Arrange
    table = DynamoDBCache().table
    first = acquire_lock(table, 'job:2', ttl_seconds=300)

    # Act
    second = acquire_lock(table, 'job:2', ttl_seconds=300)

    # Assert
    assert first is not None
    assert second is None
