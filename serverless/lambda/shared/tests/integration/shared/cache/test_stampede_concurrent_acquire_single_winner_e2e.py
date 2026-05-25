"""
Given multiples invocadores concurrentes (thundering herd) compitiendo
     por el mismo lock distribuido,
When todos llaman acquire_lock simultaneamente via ThreadPoolExecutor,
Then exactamente UNO obtiene el lock y el resto recibe None.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from shared.cache import DynamoDBCache
from shared.cache.stampede import acquire_lock

pytestmark = pytest.mark.integration


def test_stampede_concurrent_acquire_single_winner_e2e(
    cache_table: str,
) -> None:
    """8 acquire_lock concurrentes sobre un key: 1 gana, 7 reciben None."""
    # Arrange
    table = DynamoDBCache().table

    def _try_acquire(_: int) -> str | None:
        return acquire_lock(table, 'herd:1', ttl_seconds=300)

    # Act
    with ThreadPoolExecutor(max_workers=8) as pool:
        holders = list(pool.map(_try_acquire, range(8)))

    # Assert
    winners = [h for h in holders if h is not None]
    losers = [h for h in holders if h is None]
    assert len(winners) == 1
    assert len(losers) == 7
