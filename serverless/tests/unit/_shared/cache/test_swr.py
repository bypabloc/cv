"""Tests para _shared.cache.swr (state machine FRESH/STALE/EXPIRED/MISS)."""

from __future__ import annotations

import pytest

from _shared.cache.swr import classify_status
from _shared.cache.types import CacheEntry, CacheStatus

pytestmark = pytest.mark.unit


def _entry(expires_at: int, stale_until: int) -> CacheEntry:
    return {
        'cache_key': 'k',
        'value': 'v',
        'encoding': 'json',
        'expires_at': expires_at,
        'stale_until': stale_until,
    }


class TestClassifyStatus:
    """classify_status - 4 estados."""

    def test_when_now_before_expires_then_fresh(self) -> None:
        """Given now=100, expires=200, When classify, Then FRESH."""
        entry = _entry(expires_at=200, stale_until=400)
        assert classify_status(entry, now=100) == CacheStatus.FRESH

    def test_when_now_in_swr_window_then_stale(self) -> None:
        """Given expires=200, stale_until=400, now=300, When classify, Then STALE."""
        entry = _entry(expires_at=200, stale_until=400)
        assert classify_status(entry, now=300) == CacheStatus.STALE

    def test_when_now_past_stale_until_then_expired(self) -> None:
        """Given stale_until=400, now=500, When classify, Then EXPIRED."""
        entry = _entry(expires_at=200, stale_until=400)
        assert classify_status(entry, now=500) == CacheStatus.EXPIRED

    def test_when_entry_none_then_miss(self) -> None:
        """Given entry=None, When classify, Then MISS."""
        assert classify_status(None) == CacheStatus.MISS

    def test_when_stale_until_equals_expires_then_no_swr_window(self) -> None:
        """
        Given stale_until == expires_at (sin SWR),
        When now == expires_at,
        Then directamente EXPIRED (no STALE).
        """
        entry = _entry(expires_at=200, stale_until=200)
        assert classify_status(entry, now=200) == CacheStatus.EXPIRED
        assert classify_status(entry, now=199) == CacheStatus.FRESH
