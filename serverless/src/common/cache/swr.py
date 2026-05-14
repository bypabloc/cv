"""
Stale-While-Revalidate (SWR) state machine.

Dada un item con `expires_at` y `stale_until` (ambos Unix timestamps en
seconds), classify_status(now) determina si:
- FRESH:   now < expires_at -> usar valor sin recomputar
- STALE:   expires_at <= now < stale_until -> usar + recomputar async
- EXPIRED: now >= stale_until -> recompute sync (con lock)

Si stale_until == expires_at, comportamiento TTL clasico (no SWR window).
"""

from __future__ import annotations

import time

from common.cache.types import CacheEntry, CacheStatus


def classify_status(
    entry: CacheEntry | None,
    *,
    now: int | None = None,
) -> CacheStatus:
    """
    Determina el estado actual de un cache entry.

    Args:
        entry: CacheEntry o None (si DynamoDB devolvio None).
        now: timestamp de referencia (default time.time()).

    Returns:
        CacheStatus.

    Examples:
        >>> from common.cache.types import CacheEntry
        >>> entry = CacheEntry(cache_key='k', value='v', encoding='json',
        ...                    expires_at=200, stale_until=400)
        >>> classify_status(entry, now=100)
        <CacheStatus.FRESH: 'FRESH'>
        >>> classify_status(entry, now=300)
        <CacheStatus.STALE: 'STALE'>
        >>> classify_status(entry, now=500)
        <CacheStatus.EXPIRED: 'EXPIRED'>
        >>> classify_status(None)
        <CacheStatus.MISS: 'MISS'>
    """
    if entry is None:
        return CacheStatus.MISS

    current = now if now is not None else int(time.time())
    expires_at = entry.get('expires_at', 0)
    stale_until = entry.get('stale_until', expires_at)

    if current < expires_at:
        return CacheStatus.FRESH

    if current < stale_until:
        return CacheStatus.STALE

    return CacheStatus.EXPIRED
