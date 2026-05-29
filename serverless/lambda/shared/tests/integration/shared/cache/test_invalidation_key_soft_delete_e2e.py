"""
Given un key fresh en la tabla cache,
When DynamoDBCache.invalidate(key=...) hace el soft delete (TTL=0),
Then el item sigue en DynamoDB pero get() lo trata como EXPIRED (None).
"""

from __future__ import annotations

import pytest
from shared.cache.client import DynamoDBCache

pytestmark = pytest.mark.integration


def test_invalidation_key_soft_delete_e2e(cache_table: str) -> None:
    """invalidate(key) deja el item pero con expires_at=0 -> get() None."""
    # Arrange
    cache = DynamoDBCache()
    cache.set('cfg:1', {'flag': True}, ttl=300)

    # Act
    count = cache.invalidate(key='cfg:1')
    fetched = cache.get('cfg:1')
    raw = cache.get_entry('cfg:1')

    # Assert
    assert count == 1
    assert fetched is None
    assert raw is not None
    assert raw['expires_at'] == 0
