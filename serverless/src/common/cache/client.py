"""
DynamoDBCache: cliente principal del cache module.

API:
- get(key) -> Any | None  (returns deserialized value si fresh, None si miss/expired)
- get_entry(key) -> CacheEntry | None  (returns el raw entry para classify_status)
- set(key, value, ttl, *, stale_for, tags, metadata)
- delete(key)
- invalidate(tag)

Por defecto usa la table `portfolio-cache-{stage}` derivada de env vars.
"""

from __future__ import annotations

import os
import time
from typing import Any

import boto3

from common.cache.invalidation import invalidate_by_tag, invalidate_key
from common.cache.serializers import deserialize, serialize, serialize_entry
from common.cache.swr import classify_status
from common.cache.types import CacheEntry, CacheStatus


class DynamoDBCache:
    """Cliente de cache key-value con DynamoDB TTL."""

    def __init__(self, table_name: str | None = None) -> None:
        """
        Args:
            table_name: nombre fisico de la tabla; default leido de env
                        CACHE_TABLE_NAME.
        """
        resolved = table_name or os.environ.get(
            'CACHE_TABLE_NAME', 'portfolio-cache-dev'
        )
        # Instanciar boto3 Resource aqui (no module-scope) para que cada
        # invocacion en Lambda warm reuse la conexion HTTP via _session_cache,
        # pero los tests con moto pueden interceptar.
        region = os.environ.get('AWS_REGION', 'us-east-1')
        self._table = boto3.resource('dynamodb', region_name=region).Table(resolved)
        self.table_name = resolved

    def get_entry(self, key: str) -> CacheEntry | None:
        """
        Lee el raw CacheEntry de DynamoDB.

        Returns:
            CacheEntry o None si no existe.
        """
        result = self._table.get_item(Key={'cache_key': key})
        item = result.get('Item')
        if item is None:
            return None
        # DynamoDB devuelve Decimal para numeros; convertir a int
        item['expires_at'] = int(item.get('expires_at', 0))
        item['stale_until'] = int(item.get('stale_until', item['expires_at']))
        return item  # type: ignore[return-value]

    def get(self, key: str) -> Any | None:
        """
        Lee y deserializa el value. Returns None si MISS o EXPIRED.

        Para SWR (fresh/stale logic) usar `get_entry` + `classify_status`.
        """
        entry = self.get_entry(key)
        if entry is None:
            return None

        status = classify_status(entry)
        if status == CacheStatus.EXPIRED:
            return None

        return deserialize(entry['value'], entry['encoding'])

    def set(
        self,
        key: str,
        value: Any,
        *,
        ttl: int,
        stale_for: int | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Almacena value con TTL.

        Args:
            key: cache key (string).
            value: cualquier JSON-serializable o bytes.
            ttl: segundos hasta `expires_at` (cuando pasa a stale o expired).
            stale_for: segundos adicionales despues de expires_at en los que
                       el value es "stale" pero usable (SWR window).
                       None = sin SWR (stale_until = expires_at).
            tags: tags para invalidacion bulk.
            metadata: dict opcional para context (no se usa para logica).
        """
        now = int(time.time())
        expires_at = now + ttl
        stale_until = expires_at + (stale_for or 0)

        ser_value, encoding = serialize(value)

        entry: CacheEntry = {
            'cache_key': key,
            'value': ser_value,
            'encoding': encoding,
            'expires_at': expires_at,
            'stale_until': stale_until,
        }
        if tags:
            entry['tags'] = tags
        if metadata:
            entry['metadata'] = metadata

        self._table.put_item(Item=serialize_entry(entry))

    def delete(self, key: str) -> None:
        """Elimina el key del cache (hard delete)."""
        self._table.delete_item(Key={'cache_key': key})

    def invalidate(self, *, tag: str | None = None, key: str | None = None) -> int:
        """
        Invalida items via tag (soft delete) o key directo.

        Args:
            tag: tag a invalidar (mutuamente exclusivo con key).
            key: key especifico a invalidar (soft delete via TTL=0).

        Returns:
            Cantidad de items invalidados.
        """
        if tag is None and key is None:
            msg = 'invalidate() requiere tag o key'
            raise ValueError(msg)
        if tag is not None and key is not None:
            msg = 'invalidate() acepta tag O key, no ambos'
            raise ValueError(msg)

        if tag is not None:
            return invalidate_by_tag(self._table, tag)

        invalidate_key(self._table, key)  # type: ignore[arg-type]
        return 1

    @property
    def table(self) -> Any:
        """Acceso al boto3 Table (para uso avanzado en stampede.py)."""
        return self._table
