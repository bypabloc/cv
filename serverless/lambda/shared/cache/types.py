"""
TypedDicts y enums del cache module.

CacheStatus: estado del item dado el tiempo actual
- FRESH:   now < expires_at
- STALE:   expires_at <= now < stale_until (devolver + refresh async)
- EXPIRED: now >= stale_until (recompute sync via lock)
- MISS:    item no existe en DynamoDB

CacheEntry: shape del item en DynamoDB
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, NotRequired, TypedDict


class CacheStatus(StrEnum):
    """Estado de un cache item respecto al tiempo actual."""

    FRESH = 'FRESH'
    STALE = 'STALE'
    EXPIRED = 'EXPIRED'
    MISS = 'MISS'


class CacheEntry(TypedDict):
    """Shape del item almacenado en DynamoDB cache table."""

    # Primary key
    cache_key: str

    # Valor serializado (JSON string para tipos JSON-safe, base64 para bytes)
    value: str

    # Indicador de tipo de serializacion: 'json' | 'bytes_b64'
    encoding: str

    # Unix timestamp en seconds (cuando el valor pasa a stale)
    expires_at: int

    # Unix timestamp en seconds (cuando el valor pasa a expired, fuera de SWR window)
    # Si expires_at == stale_until, no hay SWR (comportamiento clasico TTL).
    stale_until: int

    # Tags para invalidacion bulk (ej: ['secrets', 'ssm'])
    tags: NotRequired[list[str]]

    # Metadata opcional (key origin, version, etc.)
    metadata: NotRequired[dict[str, Any]]


class LockEntry(TypedDict):
    """Shape del lock distribuido (item separado en la misma tabla)."""

    cache_key: str  # 'lock:<original_key>'
    value: str  # holder_id (random UUID del invocador que adquirio)
    expires_at: int  # Unix timestamp; AWS borra el lock auto si crash
    encoding: str  # 'lock' marker
    stale_until: int  # = expires_at para locks (no SWR)
