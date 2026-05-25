"""
Given una tabla cache DynamoDB real (moto),
When DynamoDBCache hace set() de un dict y luego get(),
Then el value se persiste y se recupera identico tras el roundtrip.
"""

from __future__ import annotations

import pytest
from shared.cache import DynamoDBCache

pytestmark = pytest.mark.integration


def test_client_set_get_roundtrip_e2e(cache_table: str) -> None:
    """set() de un dict -> get() devuelve el mismo dict deserializado."""
    # Arrange
    cache = DynamoDBCache()
    value = {'name': 'Pablo', 'count': 7, 'tags': ['a', 'b']}

    # Act
    cache.set('user:42', value, ttl=300)
    fetched = cache.get('user:42')

    # Assert
    assert fetched == {'name': 'Pablo', 'count': 7, 'tags': ['a', 'b']}
