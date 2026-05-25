"""
Given un entry persistido con TTL + ventana SWR en la tabla cache real,
When el tiempo avanza a traves de las 3 fases,
Then classify_status sobre el entry leido de DynamoDB reporta
     FRESH -> STALE -> EXPIRED en cada fase.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from freezegun import freeze_time
from shared.cache import DynamoDBCache
from shared.cache.swr import classify_status
from shared.cache.types import CacheStatus

pytestmark = pytest.mark.integration


def test_swr_fresh_stale_expired_transitions_e2e(cache_table: str) -> None:
    """Un entry con ttl=10/stale_for=20: FRESH, luego STALE, luego EXPIRED."""
    # Arrange
    cache = DynamoDBCache()
    frozen = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)
    base = int(frozen.timestamp())
    with freeze_time(frozen):
        # expires_at = base+10, stale_until = base+30.
        cache.set('swr:1', 'payload', ttl=10, stale_for=20)

    # Act
    entry = cache.get_entry('swr:1')
    fresh = classify_status(entry, now=base + 5)
    stale = classify_status(entry, now=base + 15)
    expired = classify_status(entry, now=base + 40)

    # Assert
    assert fresh == CacheStatus.FRESH
    assert stale == CacheStatus.STALE
    assert expired == CacheStatus.EXPIRED
