"""
Given que ya existe (o no) un item con un PK,
When se llama .put_if_absent(),
Then escribe y devuelve True solo si no existia (AC-4).
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models import CacheItem


def _lock_item(key: str = 'lock:resource') -> CacheItem:
    """Construye un CacheItem que representa un lock distribuido."""
    return CacheItem(
        cache_key=key,
        value='holder-abc',
        encoding='lock',
        expires_at=1715000015,
        stale_until=1715000015,
    )


@pytest.mark.usefixtures('dynamodb_tables')
def test_put_if_absent_writes_when_key_free() -> None:
    """put_if_absent() escribe y devuelve True si el key no existe."""
    # Act
    written = _lock_item().put_if_absent()

    # Assert
    assert written is True
    assert CacheItem.get('lock:resource') is not None


@pytest.mark.usefixtures('dynamodb_tables')
def test_put_if_absent_skips_when_key_taken() -> None:
    """put_if_absent() devuelve False si el key ya existe."""
    # Arrange
    _lock_item().put_if_absent()

    # Act
    second = _lock_item().put_if_absent()

    # Assert
    assert second is False
