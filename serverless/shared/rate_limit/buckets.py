"""
Sliding window weighted: cuenta requests por (ip, endpoint, window).

Algoritmo (detallado en `.claude/docs/serverless-rate-limit/02-sliding-window-weighted-deep-dive.md`):

1. Para una window de N segundos, el algoritmo lee 2 buckets:
   - current: ventana actual [now - now%N, now)
   - previous: ventana anterior [previous_start, previous_start + N)

2. Effective count = current.count + previous.count * (1 - elapsed_fraction)
   donde `elapsed_fraction = (now - current_start) / N`

3. Esto distribuye el conteo "smoothly" en la transicion entre buckets,
   evitando el bug clasico del fixed window donde 2 windows back-to-back
   permiten 2x el limite real.

Bucket schema:
    PK: bucket_key (string)   # 'ip#1.2.3.4#endpoint#/contact#window#1715000000'
    count: number             # incrementado con UpdateItem ADD
    turnstile_tokens: number  # contador separado para auto-blacklist
    expires_at: number (TTL)  # window_start + window_seconds * 2 (mantener prev)
"""

from __future__ import annotations

import os
import time
from typing import Any

from shared.dynamodb_client import get_table


def _buckets_table() -> Any:
    # get_table reusa el resource DynamoDB module-scope (shared.dynamodb_client)
    # en vez de crear uno nuevo por llamada (~150ms cold start por invocacion).
    table_name = os.environ.get(
        'RATE_LIMIT_BUCKETS_TABLE_NAME', 'portfolio-rate-limit-buckets-dev'
    )
    return get_table(table_name)


def _window_start(now: int, window_seconds: int) -> int:
    """Inicio del bucket que contiene `now` (round down a multiplo de window)."""
    return (now // window_seconds) * window_seconds


def _bucket_key(*, ip: str, endpoint: str, window_start: int) -> str:
    """Construye el bucket_key string."""
    return f'ip#{ip}#endpoint#{endpoint}#window#{window_start}'


def get_effective_count(
    *,
    ip: str,
    endpoint: str,
    window_seconds: int,
    now: int | None = None,
) -> float:
    """
    Calcula el effective count sliding window weighted.

    Lee 2 buckets (current + previous) y aplica el algoritmo de
    interpolacion lineal.

    Returns:
        float (puede ser fraccional por el weighted).
    """
    current_time = now if now is not None else int(time.time())
    table = _buckets_table()
    current_start = _window_start(current_time, window_seconds)
    previous_start = current_start - window_seconds

    # Leer current bucket
    current_key = _bucket_key(ip=ip, endpoint=endpoint, window_start=current_start)
    current_item = table.get_item(Key={'bucket_key': current_key}).get('Item') or {}
    current_count = int(current_item.get('count', 0))

    # Leer previous bucket
    previous_key = _bucket_key(ip=ip, endpoint=endpoint, window_start=previous_start)
    previous_item = table.get_item(Key={'bucket_key': previous_key}).get('Item') or {}
    previous_count = int(previous_item.get('count', 0))

    # Fraction del current window transcurrido
    elapsed_in_current = current_time - current_start
    elapsed_fraction = elapsed_in_current / window_seconds
    previous_weight = 1.0 - elapsed_fraction

    return current_count + previous_count * previous_weight


def increment_bucket(
    *,
    ip: str,
    endpoint: str,
    window_seconds: int,
    turnstile_validated: bool = False,
    now: int | None = None,
) -> dict[str, int]:
    """
    Atomic INCREMENT del bucket actual.

    Args:
        ip: IP del cliente.
        endpoint: path del endpoint.
        window_seconds: longitud de la ventana.
        turnstile_validated: si True, tambien incrementa turnstile_tokens.
        now: timestamp (default: time.time()).

    Returns:
        Dict con `count` y `turnstile_tokens` actualizados.
    """
    current_time = now if now is not None else int(time.time())
    table = _buckets_table()
    current_start = _window_start(current_time, window_seconds)
    key = _bucket_key(ip=ip, endpoint=endpoint, window_start=current_start)
    # TTL: borrar el bucket 2 ventanas despues (para que el next bucket
    # tenga "previous" correcto disponible)
    expires_at = current_start + window_seconds * 2

    # DynamoDB UpdateExpression: solo UNA section ADD, una SET, etc.
    # Combinar ambos increments en el mismo ADD.
    if turnstile_validated:
        update_expr = 'ADD #count :inc, turnstile_tokens :tt SET expires_at = :exp'
        expr_values: dict[str, Any] = {
            ':inc': 1,
            ':tt': 1,
            ':exp': expires_at,
        }
    else:
        update_expr = 'ADD #count :inc SET expires_at = :exp'
        expr_values = {':inc': 1, ':exp': expires_at}
    expr_names = {'#count': 'count'}

    result = table.update_item(
        Key={'bucket_key': key},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
        ReturnValues='ALL_NEW',
    )
    attrs = result.get('Attributes', {})
    return {
        'count': int(attrs.get('count', 0)),
        'turnstile_tokens': int(attrs.get('turnstile_tokens', 0)),
    }
