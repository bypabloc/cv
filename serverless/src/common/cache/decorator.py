"""
@cached decorator: memoization persistente via DynamoDB con SWR + locks.

Uso:

    from common.cache import cached

    @cached(ttl=300, namespace='ssm', tags=['secrets'])
    def get_turnstile_secret() -> str:
        return ssm.get_parameter('/portfolio/turnstile-secret')['Value']

Comportamiento:
1. Hash de args + kwargs -> cache_key
2. cache.get_entry(key)
   - FRESH:   return cached value (HIT)
   - STALE:   return cached value + log "stale, would refresh async"
              (en Lambda async refresh es fragil; preferimos servir stale
              y dejar que el proximo invocador haga el refresh sync)
   - MISS o EXPIRED:
     - acquire_lock(key) con TTL 15s
     - si lock OK: compute fn(...), cache.set(value, ttl, stale_for, tags),
                   release_lock, return value
     - si lock NO disponible: busy-wait 500ms y retry; si stale entry
                              disponible, return stale; sino re-raise

Limitaciones:
- Solo cachea funciones puras (no side-effects que no esten en el resultado).
- Args deben ser hashables (tuples/strings/ints/None ok; dicts NO).
"""

from __future__ import annotations

import functools
import hashlib
import json
import time
from collections.abc import Callable
from typing import Any, TypeVar

from common.cache.client import DynamoDBCache
from common.cache.serializers import deserialize
from common.cache.stampede import acquire_lock, release_lock
from common.cache.swr import classify_status
from common.cache.types import CacheStatus
from common.logger import logger

F = TypeVar('F', bound=Callable[..., Any])


def _hash_call(fn_name: str, args: tuple, kwargs: dict) -> str:
    """Hash determinista de la llamada a la funcion para usar como cache key."""
    try:
        signature = json.dumps(
            {'fn': fn_name, 'args': args, 'kwargs': kwargs},
            sort_keys=True,
            default=str,
        )
    except (TypeError, ValueError):
        signature = repr((fn_name, args, kwargs))
    return hashlib.sha256(signature.encode()).hexdigest()[:24]


def cached(
    *,
    ttl: int,
    namespace: str = 'default',
    stale_for: int | None = None,
    tags: list[str] | None = None,
    lock_timeout: int = 15,
    busy_wait_ms: int = 500,
) -> Callable[[F], F]:
    """
    Decorator: memoizacion DynamoDB con SWR + lock distribuido.

    Args:
        ttl: segundos hasta expirar.
        namespace: prefijo para el cache_key (evita colisiones entre funciones).
        stale_for: ventana SWR despues de expirar.
        tags: tags para invalidacion bulk.
        lock_timeout: cuanto retener el lock antes de soltarlo (default 15s).
        busy_wait_ms: cuanto esperar antes de retry si lock ocupado.

    Returns:
        Decorator.
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = DynamoDBCache()
            key = f'{namespace}:{fn.__name__}:{_hash_call(fn.__name__, args, kwargs)}'

            entry = cache.get_entry(key)
            status = classify_status(entry)

            if status == CacheStatus.FRESH and entry is not None:
                return deserialize(entry['value'], entry['encoding'])

            # STALE: devolver stale value y NO refrescar (en Lambda async
            # refresh es fragil). El proximo invocador hara el refresh sync.
            if status == CacheStatus.STALE and entry is not None:
                logger.debug(
                    'cache stale, serving cached',
                    extra={'cache_key': key},
                )
                return deserialize(entry['value'], entry['encoding'])

            # MISS o EXPIRED: intentar adquirir lock para recompute
            holder = acquire_lock(
                cache.table, key, ttl_seconds=lock_timeout
            )
            if holder is None:
                # Lock ocupado por otro. Busy-wait y retry.
                time.sleep(busy_wait_ms / 1000.0)
                retry_entry = cache.get_entry(key)
                retry_status = classify_status(retry_entry)
                if (
                    retry_status in (CacheStatus.FRESH, CacheStatus.STALE)
                    and retry_entry is not None
                ):
                    return deserialize(retry_entry['value'], retry_entry['encoding'])
                # Si despues del busy-wait el otro holder no termino,
                # recompute sin lock (mejor servir resultado que fallar)
                logger.warning(
                    'cache lock busy after busy-wait, recomputing without lock',
                    extra={'cache_key': key},
                )
                result = fn(*args, **kwargs)
                cache.set(
                    key, result, ttl=ttl, stale_for=stale_for, tags=tags,
                )
                return result

            # Tenemos el lock. Compute + set + release
            try:
                result = fn(*args, **kwargs)
                cache.set(
                    key, result, ttl=ttl, stale_for=stale_for, tags=tags,
                )
                return result
            finally:
                release_lock(cache.table, key, holder)

        return wrapper  # type: ignore[return-value]

    return decorator
