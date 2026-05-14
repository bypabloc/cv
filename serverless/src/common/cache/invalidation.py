"""
Tag-based invalidation: invalidar todos los items con un tag dado.

Patron:
- Cada item puede tener tags=['secrets', 'ssm'] al cache.set()
- invalidate(tag='secrets') setea expires_at=0 en TODOS esos items
  (soft delete - TTL service borra dentro de 48h sin costo WCU)

DynamoDB no soporta query por non-key attribute directamente. Hacemos
scan con filter sobre la tabla cache. A escala portfolio (~100 items),
el scan completo cuesta <1 RCU. A escala mayor, considerar GSI.
"""

from __future__ import annotations

from typing import Any


def invalidate_by_tag(table: Any, tag: str) -> int:
    """
    Setea expires_at=0 en todos los items con el tag dado.

    Args:
        table: boto3 DynamoDB Table.
        tag: tag a invalidar.

    Returns:
        Cantidad de items invalidados.
    """
    invalidated = 0
    paginator_kwargs: dict[str, Any] = {
        'FilterExpression': 'contains(tags, :tag)',
        'ExpressionAttributeValues': {':tag': tag},
        'ProjectionExpression': 'cache_key',
    }
    last_key: dict[str, Any] | None = None
    while True:
        kwargs = dict(paginator_kwargs)
        if last_key:
            kwargs['ExclusiveStartKey'] = last_key
        result = table.scan(**kwargs)

        for item in result.get('Items', []):
            table.update_item(
                Key={'cache_key': item['cache_key']},
                UpdateExpression='SET expires_at = :zero, stale_until = :zero',
                ExpressionAttributeValues={':zero': 0},
            )
            invalidated += 1

        last_key = result.get('LastEvaluatedKey')
        if not last_key:
            break

    return invalidated


def invalidate_key(table: Any, cache_key: str) -> bool:
    """
    Invalidacion directa de un key especifico (soft delete via TTL=0).

    Args:
        table: boto3 DynamoDB Table.
        cache_key: key a invalidar.

    Returns:
        True (siempre, idempotente).
    """
    table.update_item(
        Key={'cache_key': cache_key},
        UpdateExpression='SET expires_at = :zero, stale_until = :zero',
        ExpressionAttributeValues={':zero': 0},
    )
    return True
