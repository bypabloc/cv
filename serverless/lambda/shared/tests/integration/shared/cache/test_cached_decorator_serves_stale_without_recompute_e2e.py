"""
Given una funcion @cached con SWR window cuyo entry quedo STALE,
When se la vuelve a invocar dentro de la ventana stale,
Then sirve el valor stale cacheado SIN volver a computar
     (en Lambda el refresh async es fragil, se sirve stale).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time
from shared.cache.decorator import cached

pytestmark = pytest.mark.integration


def test_cached_decorator_serves_stale_without_recompute_e2e(
    cache_table: str,
) -> None:
    """@cached STALE: sirve el cacheado sin recomputar dentro del SWR."""
    # Arrange
    calls: list[int] = []

    @cached(ttl=10, stale_for=600, namespace='it')
    def value() -> int:
        calls.append(1)
        return len(calls) * 100

    base = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)

    # Act
    with freeze_time(base):
        first = value()  # MISS -> computa, expires en base+10
    # Avanzar 30s: entry pasa a STALE (10 < 30 < 10+600).
    with freeze_time(base + timedelta(seconds=30)):
        stale = value()

    # Assert
    assert first == 100
    assert stale == 100
    assert calls == [1]
