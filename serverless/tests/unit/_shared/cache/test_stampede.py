"""Tests para _shared.cache.stampede (lock distribuido)."""

from __future__ import annotations

import time

import pytest

from _shared.cache.client import DynamoDBCache
from _shared.cache.stampede import acquire_lock, release_lock

pytestmark = pytest.mark.unit


class TestAcquireRelease:
    """acquire_lock / release_lock - happy path + concurrency."""

    def test_when_no_lock_exists_then_acquire_returns_holder_id(
        self, cache_table: str
    ) -> None:
        """
        Given lock no existente,
        When acquire_lock,
        Then retorna holder_id (UUID).
        """
        cache = DynamoDBCache(table_name=cache_table)

        holder = acquire_lock(cache.table, 'key1', ttl_seconds=15)

        assert holder is not None
        assert len(holder) >= 32  # UUID hex length

    def test_when_lock_exists_then_second_acquire_returns_none(
        self, cache_table: str
    ) -> None:
        """
        Given lock ya tomado,
        When otro intenta acquire_lock,
        Then retorna None.
        """
        cache = DynamoDBCache(table_name=cache_table)

        first = acquire_lock(cache.table, 'key2', ttl_seconds=15)
        second = acquire_lock(cache.table, 'key2', ttl_seconds=15)

        assert first is not None
        assert second is None

    def test_when_release_with_correct_holder_then_returns_true(
        self, cache_table: str
    ) -> None:
        """
        Given lock con holder=X,
        When release_lock(X),
        Then retorna True.
        """
        cache = DynamoDBCache(table_name=cache_table)

        holder = acquire_lock(cache.table, 'key3', ttl_seconds=15)
        assert holder is not None

        released = release_lock(cache.table, 'key3', holder)

        assert released is True

    def test_when_release_with_wrong_holder_then_returns_false(
        self, cache_table: str
    ) -> None:
        """
        Given lock con holder=A,
        When release_lock con holder=B,
        Then retorna False (no libera lock ajeno).
        """
        cache = DynamoDBCache(table_name=cache_table)
        holder_a = acquire_lock(cache.table, 'key4', ttl_seconds=15)
        assert holder_a is not None

        released = release_lock(cache.table, 'key4', 'wrong-holder')

        assert released is False

    def test_after_release_then_can_reacquire(
        self, cache_table: str
    ) -> None:
        """
        Given acquire + release,
        When acquire de nuevo,
        Then retorna nuevo holder_id.
        """
        cache = DynamoDBCache(table_name=cache_table)

        h1 = acquire_lock(cache.table, 'key5', ttl_seconds=15)
        assert h1 is not None
        release_lock(cache.table, 'key5', h1)

        h2 = acquire_lock(cache.table, 'key5', ttl_seconds=15)

        assert h2 is not None
        assert h2 != h1

    def test_when_lock_expired_then_can_reacquire(
        self, cache_table: str
    ) -> None:
        """
        Given lock con ttl=1s + sleep 2s,
        When acquire_lock denuevo,
        Then retorna nuevo holder (expired -> condition matchea expires_at < :now).
        """
        cache = DynamoDBCache(table_name=cache_table)

        h1 = acquire_lock(cache.table, 'key6', ttl_seconds=1)
        assert h1 is not None
        time.sleep(2)

        h2 = acquire_lock(cache.table, 'key6', ttl_seconds=15)

        assert h2 is not None
        assert h2 != h1
