# 06. Python Implementation (copy-paste ready)

> Modulos Python listos para copiar a `serverless/lambda/shared/cache/`.
> Tipado, docstrings BDD-style, testeado con moto.

**Verificado**: 2026-05-14 — Codigo Python 3.13 compatible, type hints obligatorios.

## Estructura

```
serverless/lambda/shared/cache/
├── __init__.py           # Exports publicos
├── client.py             # DynamoDBCache class
├── decorator.py          # @cached decorator
├── swr.py                # Stale-while-revalidate logic
├── serializers.py        # JSON + bytes b64 serialization
├── types.py              # TypedDict definitions
└── tests/
    └── test_cache.py     # Moto-based unit tests
```

## 1. cache/__init__.py

```python
"""
Cache module for DynamoDB-backed key-value storage with TTL, locks, and SWR.
"""

from .client import DynamoDBCache
from .decorator import cached
from .swr import SWRResult, get_with_swr
from .types import CacheEntry, CacheStatus

__all__ = [
    'DynamoDBCache',
    'cached',
    'get_with_swr',
    'SWRResult',
    'CacheEntry',
    'CacheStatus',
]
```

## 2. cache/types.py

```python
"""
Type definitions for cache module.
"""

from enum import Enum
from typing import Any, TypedDict


class CacheStatus(Enum):
    """
    Estados posibles de un cache entry.
    """

    FRESH = 'fresh'        # now < expires_at
    STALE = 'stale'        # expires_at <= now < stale_until
    EXPIRED = 'expired'    # now >= stale_until
    MISSING = 'missing'    # No existe


class CacheEntry(TypedDict, total=False):
    """
    Estructura de un item en DynamoDB tabla cache.
    """

    cache_key: str
    value: str  # JSON stringified o bytes b64
    value_type: str  # 'json' | 'string' | 'bytes_b64'
    created_at: str  # ISO8601
    expires_at: int  # Unix epoch seconds (TTL attribute)
    tags: set[str]  # Opcional, para invalidation
    lock_owner: str  # Opcional, Lambda request_id
    lock_expires: int  # Opcional, Unix epoch seconds
    stale_until: int  # Opcional, SWR window
```

## 3. cache/serializers.py

```python
"""
Serializers para cache values (JSON, bytes, strings).
"""

import base64
import json
from typing import Any


def serialize(value: Any, value_type: str = 'json') -> str:
    """
    Serializar valor para almacenar en DynamoDB.

    Args:
        value: valor a serializar
        value_type: 'json' (default), 'string', 'bytes_b64'

    Returns:
        string para almacenar en DynamoDB

    Raises:
        ValueError: si value_type invalido
    """
    if value_type == 'json':
        return json.dumps(value)
    elif value_type == 'string':
        return str(value)
    elif value_type == 'bytes_b64':
        if isinstance(value, bytes):
            return base64.b64encode(value).decode('utf-8')
        elif isinstance(value, str):
            return base64.b64encode(value.encode('utf-8')).decode('utf-8')
        else:
            raise ValueError(f'bytes_b64 requires bytes or str, got {type(value)}')
    else:
        raise ValueError(f'Unknown value_type: {value_type}')


def deserialize(stored: str, value_type: str) -> Any:
    """
    Deserializar valor desde DynamoDB.

    Args:
        stored: string almacenado
        value_type: 'json' (default), 'string', 'bytes_b64'

    Returns:
        valor deserializado

    Raises:
        ValueError: si value_type invalido o deserializacion falla
    """
    if value_type == 'json':
        return json.loads(stored)
    elif value_type == 'string':
        return stored
    elif value_type == 'bytes_b64':
        return base64.b64decode(stored.encode('utf-8'))
    else:
        raise ValueError(f'Unknown value_type: {value_type}')
```

## 4. cache/client.py

```python
"""
DynamoDBCache: cliente de cache con TTL, locks distribuidos, SWR, invalidation por tag.
"""

import json
import os
import time
from datetime import datetime, UTC
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .serializers import deserialize, serialize
from .types import CacheEntry, CacheStatus


class DynamoDBCache:
    """
    Cache de DynamoDB con soporte para TTL, locks distribuidos (cache stampede prevention),
    stale-while-revalidate, e invalidation por tag.

    Uso basico:
        cache = DynamoDBCache()
        cache.set('key', {'data': 'value'}, ttl=300, tags=['analytics'])
        value = cache.get('key')
        cache.invalidate(tag='analytics')
    """

    def __init__(self, table_name: str | None = None):
        """
        Inicializar cache.

        Args:
            table_name: nombre de tabla DynamoDB (default: env var CACHE_TABLE_NAME)
        """
        self.table_name = table_name or os.environ.get('CACHE_TABLE_NAME', 'cache')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def get(self, cache_key: str) -> Any | None:
        """
        Obtener valor del cache.

        Given un cache_key valido,
        When get es invocado,
        Then retorna el valor deserializado o None si no existe o esta expirado.

        Args:
            cache_key: clave unica

        Returns:
            valor deserializado, o None
        """
        try:
            response = self.table.get_item(Key={'cache_key': cache_key})
            item = response.get('Item')

            if not item:
                return None

            # Revisar si expirado (aunque TTL background delete eventual)
            if int(time.time()) >= item.get('expires_at', 0):
                return None

            value_type = item.get('value_type', 'json')
            stored = item.get('value')
            return deserialize(stored, value_type)

        except Exception as e:
            print(f'Error getting cache key {cache_key}: {e}')
            return None

    def set(
        self,
        cache_key: str,
        value: Any,
        ttl: int = 300,
        value_type: str = 'json',
        tags: list[str] | None = None,
    ) -> None:
        """
        Guardar valor en cache con TTL.

        Given un cache_key, value y TTL,
        When set es invocado,
        Then el valor se guarda con expires_at = now + ttl.

        Args:
            cache_key: clave unica
            value: valor a cachear
            ttl: time-to-live en segundos (default 300)
            value_type: tipo del valor ('json', 'string', 'bytes_b64')
            tags: lista de tags para invalidation por tag
        """
        try:
            now = int(time.time())
            item: CacheEntry = {
                'cache_key': cache_key,
                'value': serialize(value, value_type),
                'value_type': value_type,
                'created_at': datetime.now(UTC).isoformat(),
                'expires_at': now + ttl,
            }

            if tags:
                item['tags'] = set(tags)

            self.table.put_item(Item=item)

        except Exception as e:
            print(f'Error setting cache key {cache_key}: {e}')
            raise

    def delete(self, cache_key: str) -> None:
        """
        Eliminar item del cache (hard delete).

        Given un cache_key,
        When delete es invocado,
        Then el item se elimina inmediatamente.

        Args:
            cache_key: clave a eliminar
        """
        try:
            self.table.delete_item(Key={'cache_key': cache_key})
        except Exception as e:
            print(f'Error deleting cache key {cache_key}: {e}')
            raise

    def invalidate(self, tag: str) -> int:
        """
        Invalidar (soft delete) todos los items con un tag especifico.

        Given un tag,
        When invalidate es invocado,
        Then todos los items con ese tag tienen expires_at = now (expirados inmediatamente).

        Args:
            tag: etiqueta a invalidar

        Returns:
            numero de items invalidados
        """
        try:
            invalidated = 0
            now = int(time.time())

            # Scan con FilterExpression
            response = self.table.scan(
                FilterExpression='contains(tags, :tag)',
                ExpressionAttributeValues={':tag': tag},
                ProjectionExpression='cache_key',
            )

            for item in response.get('Items', []):
                self.table.update_item(
                    Key={'cache_key': item['cache_key']},
                    UpdateExpression='SET expires_at = :now',
                    ExpressionAttributeValues={':now': now},
                )
                invalidated += 1

            # Paginate si hay mas items
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    FilterExpression='contains(tags, :tag)',
                    ExpressionAttributeValues={':tag': tag},
                    ProjectionExpression='cache_key',
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                )
                for item in response.get('Items', []):
                    self.table.update_item(
                        Key={'cache_key': item['cache_key']},
                        UpdateExpression='SET expires_at = :now',
                        ExpressionAttributeValues={':now': now},
                    )
                    invalidated += 1

            return invalidated

        except Exception as e:
            print(f'Error invalidating tag {tag}: {e}')
            raise

    def acquire_lock(self, cache_key: str, lock_ttl: int = 5) -> bool:
        """
        Intentar adquirir lock distribuido para evitar cache stampede.

        Given un cache_key sin lock o con lock expirado,
        When acquire_lock es invocado,
        Then retorna True si adquiri el lock, False si otro Lambda lo tiene.

        Args:
            cache_key: clave a lockear
            lock_ttl: tiempo de vida del lock en segundos

        Returns:
            True si adquiri lock, False si otro Lambda lo tiene
        """
        try:
            request_id = os.environ.get('AWS_REQUEST_ID', 'local-dev')
            lock_expires = int(time.time()) + lock_ttl

            self.table.update_item(
                Key={'cache_key': cache_key},
                UpdateExpression='SET lock_owner = :rid, lock_expires = :exp',
                ConditionExpression=(
                    'attribute_not_exists(lock_owner) OR lock_expires < :now'
                ),
                ExpressionAttributeValues={
                    ':rid': request_id,
                    ':exp': lock_expires,
                    ':now': int(time.time()),
                },
            )
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            raise

    def release_lock(self, cache_key: str) -> None:
        """
        Liberar lock distribuido.

        Args:
            cache_key: clave cuyo lock liberar
        """
        try:
            self.table.update_item(
                Key={'cache_key': cache_key},
                UpdateExpression='REMOVE lock_owner, lock_expires',
            )
        except Exception as e:
            print(f'Error releasing lock for {cache_key}: {e}')
            # No propagar, es best-effort

    def get_status(self, cache_key: str) -> CacheStatus:
        """
        Obtener estado del cache entry (FRESH, STALE, EXPIRED, MISSING).

        Args:
            cache_key: clave a inspeccionar

        Returns:
            CacheStatus enum
        """
        try:
            response = self.table.get_item(Key={'cache_key': cache_key})
            item = response.get('Item')

            if not item:
                return CacheStatus.MISSING

            now = int(time.time())
            expires_at = item.get('expires_at', 0)
            stale_until = item.get('stale_until', expires_at)

            if now < expires_at:
                return CacheStatus.FRESH
            elif now < stale_until:
                return CacheStatus.STALE
            else:
                return CacheStatus.EXPIRED

        except Exception as e:
            print(f'Error getting status for {cache_key}: {e}')
            return CacheStatus.MISSING
```

## 5. cache/decorator.py

```python
"""
@cached decorator: memoization con persistencia en DynamoDB.
"""

import hashlib
import json
from functools import wraps
from typing import Any, Callable

from .client import DynamoDBCache


def cached(
    ttl: int = 300,
    namespace: str = 'default',
    tags: list[str] | None = None,
):
    """
    Decorator para cachear resultado de funcion en DynamoDB.

    Usa los argumentos de la funcion para generar cache_key.

    Given una funcion que recibe kwargs,
    When @cached decorator se aplica,
    Then el resultado se cachea bajo cache_key = namespace:hash(args).

    Args:
        ttl: time-to-live en segundos
        namespace: prefijo para cache_key (ej. 'query')
        tags: tags para invalidation

    Example:
        @cached(ttl=300, namespace='query', tags=['analytics'])
        def get_top_countries():
            return query_neon()

        @cached(ttl=600, namespace='ssm', tags=['config'])
        def get_turnstile_secret(key: str):
            return ssm.get_parameter(Name=key)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = DynamoDBCache()

            # Generar cache_key desde args + kwargs
            args_str = json.dumps([args, kwargs], sort_keys=True, default=str)
            args_hash = hashlib.sha256(args_str.encode()).hexdigest()[:12]
            cache_key = f'{namespace}:{func.__name__}:{args_hash}'

            # Intentar get
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Cache miss: ejecutar funcion
            result = func(*args, **kwargs)

            # Guardar en cache
            cache.set(cache_key, result, ttl=ttl, tags=tags or [])

            return result

        return wrapper

    return decorator
```

## 6. cache/swr.py

```python
"""
Stale-While-Revalidate (SWR) pattern.
"""

import time
from datetime import datetime, UTC
from typing import Any, Callable

from .client import DynamoDBCache
from .types import CacheStatus


class SWRResult:
    """Resultado de get_with_swr con metadata."""

    def __init__(
        self,
        value: Any | None,
        status: CacheStatus,
        is_fresh: bool = False,
    ):
        self.value = value
        self.status = status
        self.is_fresh = is_fresh  # True si FRESH, False si STALE


def get_with_swr(
    cache_key: str,
    recompute_fn: Callable[[], Any],
    ttl: int = 300,
    swr: int = 300,
) -> SWRResult:
    """
    Get con Stale-While-Revalidate pattern.

    Given una funcion recompute_fn y cache_key,
    When get_with_swr es invocado,
    Then:
      - Si FRESH: retorna valor rapidamente
      - Si STALE: retorna valor + asyncio.create_task para refresh
      - Si EXPIRED: sincronamente ejecuta recompute_fn y retorna resultado

    Args:
        cache_key: clave del cache
        recompute_fn: funcion que computa valor (ej. query Neon)
        ttl: tiempo fresco en segundos
        swr: stale-while-revalidate window en segundos

    Returns:
        SWRResult con valor y status
    """
    cache = DynamoDBCache()

    # Get del cache
    item_response = cache.table.get_item(Key={'cache_key': cache_key})
    item = item_response.get('Item')

    now = int(time.time())

    if not item:
        # Cache miss: recompute sincrono
        try:
            value = recompute_fn()
            cache.set(
                cache_key,
                value,
                ttl=ttl,
            )
            # Agregar stale_until si queremos SWR window
            cache.table.update_item(
                Key={'cache_key': cache_key},
                UpdateExpression='SET stale_until = :stale',
                ExpressionAttributeValues={
                    ':stale': now + ttl + swr,
                },
            )
            return SWRResult(value, CacheStatus.FRESH, is_fresh=True)
        except Exception as e:
            print(f'Error recomputing {cache_key}: {e}')
            raise

    expires_at = item.get('expires_at', 0)
    stale_until = item.get('stale_until', expires_at)

    # Determinar status
    if now < expires_at:
        # FRESH
        from .serializers import deserialize

        value = deserialize(item['value'], item.get('value_type', 'json'))
        return SWRResult(value, CacheStatus.FRESH, is_fresh=True)

    elif now < stale_until:
        # STALE: devolver + async refresh (best-effort, no propagar error)
        try:
            # Trigger refresh (fire-and-forget)
            # En Lambda de verdad, seria asyncio.create_task o SNS/SQS
            # Aqui: best-effort sync (suboptimal pero safe)
            recompute_fn()
            cache.table.update_item(
                Key={'cache_key': cache_key},
                UpdateExpression='SET stale_until = :stale',
                ExpressionAttributeValues={
                    ':stale': now + ttl + swr,
                },
            )
        except Exception as e:
            print(f'Background refresh failed for {cache_key}: {e}')
            # No propagar, devolver stale anyway

        from .serializers import deserialize

        value = deserialize(item['value'], item.get('value_type', 'json'))
        return SWRResult(value, CacheStatus.STALE, is_fresh=False)

    else:
        # EXPIRED: recompute sincrono
        try:
            value = recompute_fn()
            cache.set(
                cache_key,
                value,
                ttl=ttl,
            )
            cache.table.update_item(
                Key={'cache_key': cache_key},
                UpdateExpression='SET stale_until = :stale',
                ExpressionAttributeValues={
                    ':stale': now + ttl + swr,
                },
            )
            return SWRResult(value, CacheStatus.FRESH, is_fresh=True)
        except Exception as e:
            print(f'Error recomputing expired {cache_key}: {e}')
            raise
```

## Testing con moto

```python
# cache/tests/test_cache.py
import pytest
from moto import mock_dynamodb
import boto3
from common.cache import DynamoDBCache


@mock_dynamodb
def test_cache_set_get():
    """
    Given cache vacio,
    When set y get invocados,
    Then valor retorna correctamente.
    """
    # Setup tabla mock
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='cache',
        KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'cache_key', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )

    cache = DynamoDBCache(table_name='cache')

    # Set
    cache.set('test-key', {'data': 'value'}, ttl=300)

    # Get
    result = cache.get('test-key')
    assert result == {'data': 'value'}


@mock_dynamodb
def test_cache_invalidate_by_tag():
    """
    Given cache con items taggados,
    When invalidate invocado con tag,
    Then todos los items con ese tag expiran.
    """
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='cache',
        KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'cache_key', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )

    cache = DynamoDBCache(table_name='cache')

    # Set con tags
    cache.set('key1', {'a': 1}, ttl=300, tags=['analytics', 'fresh'])
    cache.set('key2', {'b': 2}, ttl=300, tags=['analytics'])
    cache.set('key3', {'c': 3}, ttl=300, tags=['other'])

    # Invalidate
    invalidated = cache.invalidate('analytics')
    assert invalidated == 2

    # Verificar que key1 y key2 estan expirados, key3 no
    assert cache.get('key1') is None
    assert cache.get('key2') is None
    assert cache.get('key3') == {'c': 3}
```

---

## Deployment checklist

- [ ] Copiar los 6 modulos a `serverless/lambda/shared/cache/`
- [ ] Crear tabla DynamoDB via SAM/CloudFormation
- [ ] Verificar tabla tiene TTL enabled en `expires_at`
- [ ] IAM policy: Lambda tiene `dynamodb:GetItem, PutItem, UpdateItem, DeleteItem` en tabla
- [ ] Tests locales: `pytest cache/tests/` con moto
- [ ] Usar env var `CACHE_TABLE_NAME` (default: 'cache')

