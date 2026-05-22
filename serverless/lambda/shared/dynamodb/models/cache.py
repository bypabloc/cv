"""Modelo de la tabla `portfolio-cache-{stage}`.

Tabla key-value para el cache con TTL + SWR. PK simple `cache_key`. TTL
via `expires_at`. La misma tabla guarda items de cache normales y los
items de lock distribuido (`cache_key` con prefijo `lock:`,
`encoding='lock'`): `CacheItem` modela ambos.
"""

from __future__ import annotations

from typing import Any, ClassVar

from shared.dynamodb._schema import TableMeta
from shared.dynamodb.base import BaseModel


class CacheItem(BaseModel):
    """Un item del cache DynamoDB (entrada de cache o lock distribuido).

    `value` lleva el contenido serializado (o el holder_id si es un
    lock); `encoding` indica el tipo (`json` | `bytes_b64` | `lock`).
    `tags` y `metadata` son opcionales y se omiten del Item si estan
    vacios.
    """

    Meta: ClassVar[TableMeta] = TableMeta(
        table_env_var='CACHE_TABLE_NAME',
        table_default='portfolio-cache-dev',
        partition_key='cache_key',
        ttl_attr='expires_at',
    )

    cache_key: str
    value: str
    encoding: str
    expires_at: int
    stale_until: int
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
