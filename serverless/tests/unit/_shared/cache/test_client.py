"""Tests para _shared.cache.client (DynamoDBCache CRUD)."""

from __future__ import annotations

import pytest

from _shared.cache.client import DynamoDBCache

pytestmark = pytest.mark.unit


class TestSetGet:
    """set/get - roundtrip basico."""

    def test_when_set_then_get_returns_value(self, cache_table: str) -> None:
        """Given set('k', value), When get('k'), Then retorna value."""
        cache = DynamoDBCache(table_name=cache_table)
        cache.set('k', {'a': 1}, ttl=300)

        result = cache.get('k')

        assert result == {'a': 1}

    def test_when_get_missing_key_then_none(self, cache_table: str) -> None:
        """Given key sin set, When get, Then None."""
        cache = DynamoDBCache(table_name=cache_table)

        assert cache.get('missing') is None

    def test_when_set_bytes_then_get_returns_bytes(
        self, cache_table: str
    ) -> None:
        """Given bytes value, When set+get, Then bytes preservados."""
        cache = DynamoDBCache(table_name=cache_table)
        cache.set('k', b'binary', ttl=300)

        assert cache.get('k') == b'binary'

    def test_when_set_with_stale_for_then_entry_has_swr_window(
        self, cache_table: str
    ) -> None:
        """Given stale_for=600, When set, Then stale_until = expires_at + 600."""
        cache = DynamoDBCache(table_name=cache_table)
        cache.set('k', 'v', ttl=60, stale_for=600)

        entry = cache.get_entry('k')
        assert entry is not None
        assert entry['stale_until'] - entry['expires_at'] == 600

    def test_when_set_with_tags_then_entry_has_tags(
        self, cache_table: str
    ) -> None:
        """Given tags, When set, Then entry.tags incluye los tags."""
        cache = DynamoDBCache(table_name=cache_table)
        cache.set('k', 'v', ttl=60, tags=['a', 'b'])

        entry = cache.get_entry('k')
        assert entry is not None
        assert entry.get('tags') == ['a', 'b']


class TestDelete:
    """delete - hard delete."""

    def test_when_delete_then_get_returns_none(self, cache_table: str) -> None:
        """Given set + delete, When get, Then None."""
        cache = DynamoDBCache(table_name=cache_table)
        cache.set('k', 'v', ttl=60)

        cache.delete('k')

        assert cache.get('k') is None

    def test_when_delete_missing_then_no_error(self, cache_table: str) -> None:
        """Given key inexistente, When delete, Then no error (idempotente)."""
        cache = DynamoDBCache(table_name=cache_table)
        cache.delete('missing')  # debe ser noop


class TestInvalidate:
    """invalidate - soft delete por tag o key."""

    def test_when_invalidate_tag_then_items_get_zero_ttl(
        self, cache_table: str
    ) -> None:
        """
        Given 2 items con tag='secrets', 1 sin tag,
        When invalidate(tag='secrets'),
        Then ambos items con tag tienen expires_at=0, el otro intacto.
        """
        cache = DynamoDBCache(table_name=cache_table)
        cache.set('a', 1, ttl=3600, tags=['secrets'])
        cache.set('b', 2, ttl=3600, tags=['secrets'])
        cache.set('c', 3, ttl=3600, tags=['other'])

        count = cache.invalidate(tag='secrets')

        assert count == 2
        # a y b ahora expired
        assert cache.get('a') is None
        assert cache.get('b') is None
        # c intacto
        assert cache.get('c') == 3

    def test_when_invalidate_key_then_returns_1(
        self, cache_table: str
    ) -> None:
        """Given key, When invalidate(key=...), Then return 1 + key expired."""
        cache = DynamoDBCache(table_name=cache_table)
        cache.set('k', 'v', ttl=3600)

        count = cache.invalidate(key='k')

        assert count == 1
        assert cache.get('k') is None

    def test_when_invalidate_without_args_then_raises(
        self, cache_table: str
    ) -> None:
        """Given sin args, When invalidate, Then ValueError."""
        cache = DynamoDBCache(table_name=cache_table)

        with pytest.raises(ValueError, match='requiere tag o key'):
            cache.invalidate()

    def test_when_invalidate_both_args_then_raises(
        self, cache_table: str
    ) -> None:
        """Given tag + key, When invalidate, Then ValueError."""
        cache = DynamoDBCache(table_name=cache_table)

        with pytest.raises(ValueError, match='tag O key'):
            cache.invalidate(tag='x', key='y')
