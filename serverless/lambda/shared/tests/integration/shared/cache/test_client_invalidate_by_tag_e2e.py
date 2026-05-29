"""
Given tres keys en cache, dos con el tag 'secrets',
When DynamoDBCache.invalidate(tag='secrets') corre el Scan + soft delete,
Then los 2 keys con el tag quedan expirados y el otro sigue vivo.
"""

from __future__ import annotations

import pytest
from shared.cache.client import DynamoDBCache

pytestmark = pytest.mark.integration


def test_client_invalidate_by_tag_e2e(cache_table: str) -> None:
    """invalidate(tag) hace soft delete (TTL=0) de los items del tag."""
    # Arrange
    cache = DynamoDBCache()
    cache.set('k1', 'v1', ttl=300, tags=['secrets', 'ssm'])
    cache.set('k2', 'v2', ttl=300, tags=['secrets'])
    cache.set('k3', 'v3', ttl=300, tags=['other'])

    # Act
    invalidated = cache.invalidate(tag='secrets')

    # Assert
    assert invalidated == 2
    assert cache.get('k1') is None
    assert cache.get('k2') is None
    assert cache.get('k3') == 'v3'
