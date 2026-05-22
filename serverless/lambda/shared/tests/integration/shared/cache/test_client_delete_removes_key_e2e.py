"""
Given un key persistido en la tabla cache,
When DynamoDBCache.delete() lo elimina,
Then un get() posterior devuelve None (hard delete).
"""

from __future__ import annotations

import pytest
from shared.cache import DynamoDBCache

pytestmark = pytest.mark.integration


def test_client_delete_removes_key_e2e(cache_table: str) -> None:
    """delete() borra el item; el get() siguiente devuelve None."""
    # Arrange
    cache = DynamoDBCache()
    cache.set('temp:1', 'value', ttl=300)

    # Act
    cache.delete('temp:1')
    fetched = cache.get('temp:1')

    # Assert
    assert fetched is None
