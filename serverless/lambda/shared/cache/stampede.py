"""
Cache stampede prevention: lock distribuido con DynamoDB ConditionalWrite.

Cuando un cache item expira y muchas Lambdas concurrentes intentan
recomputarlo simultaneamente (thundering herd), el primer Lambda que
adquiere el lock recomputa; los demas se bloquean (busy-wait) o usan
stale-data si esta disponible.

Implementacion:
- PK: `lock:<original_cache_key>`
- ConditionExpression: `attribute_not_exists(cache_key)` - solo crea el
  lock si no existe.
- TTL en lock (`expires_at` Unix epoch): si holder crashea, AWS borra el
  lock dentro de 48h. Para safety propia, definir TTL corto (~15s) y
  refresh manual si el compute tarda mas.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

from botocore.exceptions import ClientError


def _lock_key(cache_key: str) -> str:
    """Prefijo `lock:` para el key del lock distribuido."""
    return f'lock:{cache_key}'


def acquire_lock(
    table: Any,
    cache_key: str,
    *,
    ttl_seconds: int = 15,
) -> str | None:
    """
    Intenta adquirir el lock para cache_key.

    Args:
        table: boto3 DynamoDB Table reference.
        cache_key: key original del cache item.
        ttl_seconds: cuanto dura el lock antes de expirar (default 15s).

    Returns:
        holder_id (UUID random) si adquirio el lock, None si ya esta
        ocupado por otro holder.
    """
    holder_id = str(uuid.uuid4())
    expires_at = int(time.time()) + ttl_seconds
    lock_pk = _lock_key(cache_key)

    try:
        table.put_item(
            Item={
                'cache_key': lock_pk,
                'value': holder_id,
                'encoding': 'lock',
                'expires_at': expires_at,
                'stale_until': expires_at,
            },
            ConditionExpression='attribute_not_exists(cache_key) OR expires_at < :now',
            ExpressionAttributeValues={':now': int(time.time())},
        )
        return holder_id
    except ClientError as e:
        # ConditionalCheckFailedException = lock ya esta ocupado
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return None
        raise


def release_lock(table: Any, cache_key: str, holder_id: str) -> bool:
    """
    Libera el lock SOLO si el holder coincide (evita liberar lock de otro).

    Args:
        table: boto3 DynamoDB Table reference.
        cache_key: key original del cache item.
        holder_id: UUID obtenido en acquire_lock().

    Returns:
        True si liberado, False si el holder no coincide (otro ya tomo el
        lock por expiry).
    """
    lock_pk = _lock_key(cache_key)
    try:
        table.delete_item(
            Key={'cache_key': lock_pk},
            ConditionExpression='#v = :holder',
            ExpressionAttributeNames={'#v': 'value'},
            ExpressionAttributeValues={':holder': holder_id},
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        raise


# XFetch (probabilistic early recomputation): reduce thundering herd al
# permitir que ALGUNAS Lambdas refresqueen el cache antes del expiry real,
# proporcional a cuanto tiempo lleva el item en cache.
# Spec: https://en.wikipedia.org/wiki/Cache_stampede#Probabilistic_early_expiration


def should_refresh_early(
    *,
    expires_at: int,
    ttl_total: int,
    beta: float = 1.0,
    now: int | None = None,
) -> bool:
    """
    Probabilistic XFetch: True si decidimos refresh antes del expiry.

    Args:
        expires_at: Unix timestamp cuando el item pasa a stale.
        ttl_total: TTL total original (segundos).
        beta: factor de agresividad (1.0 default, mas alto = mas refresh).
        now: timestamp actual (default time.time()).

    Returns:
        True si recomendado hacer refresh ahora.

    Notes:
        Implementacion simplificada: usamos random para no introducir math
        dependencies. La distribucion exacta es exponencial, aqui usamos
        un threshold lineal cerca del expiry. Para portfolio scale es
        suficiente.
    """
    current = now if now is not None else int(time.time())
    if current >= expires_at:
        return True

    # Ventana de 10% del TTL antes del expiry
    refresh_window = max(int(ttl_total * 0.1), 1)
    if current < (expires_at - refresh_window):
        return False

    # 50% prob de refresh dentro de la ventana (escalada por beta)
    rand = int.from_bytes(os.urandom(2), 'big') / 65535.0
    return rand < (0.5 * beta)
