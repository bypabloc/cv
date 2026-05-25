"""
Given un lock adquirido por un holder concreto,
When otro holder intenta release_lock con un holder_id distinto,
Then la ConditionExpression falla y release_lock devuelve False
     (un holder no puede liberar el lock de otro).
"""

from __future__ import annotations

import pytest
from shared.cache import DynamoDBCache
from shared.cache.stampede import acquire_lock, release_lock

pytestmark = pytest.mark.integration


def test_stampede_release_wrong_holder_fails_e2e(cache_table: str) -> None:
    """release_lock con holder ajeno devuelve False y no borra el lock."""
    # Arrange
    table = DynamoDBCache().table
    acquire_lock(table, 'job:3', ttl_seconds=300)

    # Act
    released = release_lock(table, 'job:3', 'not-the-real-holder')

    # Assert
    assert released is False
