"""
DynamoDBCache: cliente principal del cache module.

API:
- get(key) -> Any | None  (returns deserialized value si fresh, None si miss/expired)
- get_entry(key) -> CacheEntry | None  (returns el raw entry para classify_status)
- set(key, value, ttl, *, stale_for, tags, metadata)
- delete(key)
- invalidate(tag)

Por defecto usa la table `portfolio-cache-{stage}` derivada de env vars.

Internamente delega la persistencia al ORM (`shared.dynamodb.CacheItem`):
asi reusa el resource boto3 singleton y la conversion `Decimal`
transparente. La API publica de esta clase NO cambia — `get_entry`
sigue devolviendo un `CacheEntry` (TypedDict) que `swr`/`stampede`
consumen.
"""

from __future__ import annotations

import time
from typing import Any

from shared.cache.invalidation import invalidate_by_tag, invalidate_key
from shared.cache.serializers import deserialize, serialize
from shared.cache.swr import classify_status
from shared.cache.types import CacheEntry, CacheStatus
from shared.dynamodb import CacheItem


class DynamoDBCache:
    """Cliente de cache key-value con DynamoDB TTL."""

    def __init__(self, table_name: str | None = None) -> None:
        """
        Args:
            table_name: nombre fisico de la tabla; si se omite, se resuelve
                        igual que el ORM (`CacheItem.table_name()`): por
                        SSM en AWS, por env var / default en tests/local.
        """
        self.table_name = table_name or CacheItem.table_name()

    def _model_table(self) -> Any:
        """boto3 Table del ORM (para invalidation/stampede que usan scan)."""
        # CacheItem resuelve el nombre via env var; si el caller paso un
        # table_name explicito distinto, respetar ese.
        if self.table_name == CacheItem.table_name():
            return CacheItem._table()
        from shared.aws.dynamodb import get_table

        return get_table(self.table_name)

    def _resolve(self, key: str) -> dict[str, Any] | None:
        """Lee el item crudo de DynamoDB (o None) usando el ORM."""
        if self.table_name == CacheItem.table_name():
            item = CacheItem.get(key)
        else:
            # table_name override (poco comun): leer via Table directo.
            result = self._model_table().get_item(Key={'cache_key': key})
            raw = result.get('Item')
            return None if raw is None else dict(raw)
        return None if item is None else item.model_dump(exclude_none=True)

    def get_entry(self, key: str) -> CacheEntry | None:
        """
        Lee el raw CacheEntry de DynamoDB.

        Returns:
            CacheEntry o None si no existe.
        """
        item = self._resolve(key)
        if item is None:
            return None
        # El ORM ya convirtio Decimal -> int; asegurar las claves de SWR.
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

        item = CacheItem(
            cache_key=key,
            value=ser_value,
            encoding=encoding,
            expires_at=expires_at,
            stale_until=stale_until,
            tags=tags or None,
            metadata=metadata or None,
        )
        if self.table_name == CacheItem.table_name():
            item.save()
        else:
            self._model_table().put_item(Item=item.to_item())

    def delete(self, key: str) -> None:
        """Elimina el key del cache (hard delete)."""
        if self.table_name == CacheItem.table_name():
            CacheItem.delete(key)
        else:
            self._model_table().delete_item(Key={'cache_key': key})

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
            return invalidate_by_tag(self._model_table(), tag)

        invalidate_key(self._model_table(), key)  # type: ignore[arg-type]
        return 1

    @property
    def table(self) -> Any:
        """Acceso al boto3 Table (para uso avanzado en stampede.py)."""
        return self._model_table()
