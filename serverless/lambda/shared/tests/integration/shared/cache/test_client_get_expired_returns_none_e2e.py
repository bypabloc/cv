"""
Given un key escrito con TTL negativo (ya expirado, sin SWR window),
When DynamoDBCache.get() lo lee,
Then devuelve None porque classify_status lo marca EXPIRED.
"""

from __future__ import annotations

import pytest
from shared.cache import DynamoDBCache

pytestmark = pytest.mark.integration


def test_client_get_expired_returns_none_e2e(cache_table: str) -> None:
    """get() de un entry expirado (sin SWR) devuelve None."""
    # Arrange
    cache = DynamoDBCache()
    # ttl=-10 -> expires_at y stale_until en el pasado; status EXPIRED.
    cache.set('stale:1', 'old-value', ttl=-10)

    # Act
    fetched = cache.get('stale:1')

    # Assert
    assert fetched is None
