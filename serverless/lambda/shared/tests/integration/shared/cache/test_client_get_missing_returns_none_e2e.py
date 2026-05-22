"""
Given una tabla cache vacia,
When DynamoDBCache.get() pide un key inexistente,
Then devuelve None (cache MISS).
"""

from __future__ import annotations

import pytest
from shared.cache import DynamoDBCache

pytestmark = pytest.mark.integration


def test_client_get_missing_returns_none_e2e(cache_table: str) -> None:
    """get() de un key que nunca se escribio devuelve None."""
    # Arrange
    cache = DynamoDBCache()

    # Act
    fetched = cache.get('never-written')

    # Assert
    assert fetched is None
