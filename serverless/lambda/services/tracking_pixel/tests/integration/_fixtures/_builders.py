"""Builders compartidos de los tests de integracion del `tracking_pixel`.

Prefijo `_` para que pytest NO recolecte este archivo como tests.

Aloja:
  - constantes de payload validas (UUIDs, User-Agents),
  - `lambda_context()`: Lambda context falso para Powertools,
  - `valid_body()`: body de tracking minimo + overrides,
  - `api_gw_event()`: evento API Gateway REST proxy crudo para POST /track,
  - `tracking_table()` / `scan_tracking()`: acceso al estado persistido en
    la tabla DynamoDB emulada por moto.

Es la version de integracion de `tests/unit/_helpers.py`: misma forma de
los builders, mas helpers para inspeccionar el efecto observable en
DynamoDB tras invocar el handler end-to-end.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

# UUIDs validos reutilizables. session_id de 28 chars (>= 20), event_id
# de 32 chars (UUID hex sin guiones), event_type_id de 36 chars (UUID con
# guiones). Cumplen los limites de TrackEventModel.
SESSION_ID = 'session-uuid-1234567890abcdef'
EVENT_ID = 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
EVENT_TYPE_ID = '019e372b-e0a7-7154-8279-8829bcf6a08c'

CHROME_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    'Chrome/118.0.0.0 Safari/537.36'
)
MOBILE_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 '
    'Mobile/15E148 Safari/604.1'
)
BOT_UA = (
    'Mozilla/5.0 (compatible; Googlebot/2.1; '
    '+http://www.google.com/bot.html)'
)

TRACKING_TABLE_NAME = 'portfolio-tracking-test'
CACHE_TABLE_NAME = 'portfolio-cache-test'


def lambda_context() -> MagicMock:
    """Devuelve un Lambda context falso valido para Powertools.

    `logger.inject_lambda_context` lee `function_name`,
    `memory_limit_in_mb`, `invoked_function_arn` y `aws_request_id`.
    """
    ctx = MagicMock()
    ctx.function_name = 'portfolio-tracking-pixel-test'
    ctx.memory_limit_in_mb = 256
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:'
        'portfolio-tracking-pixel-test'
    )
    ctx.aws_request_id = 'test-request-id'
    ctx.get_remaining_time_in_millis = lambda: 10000
    return ctx


def valid_body(**overrides: Any) -> dict[str, Any]:
    """Devuelve un body de tracking valido (campos minimos + overrides)."""
    body: dict[str, Any] = {
        'session_id': SESSION_ID,
        'event_id': EVENT_ID,
        'event_type_id': EVENT_TYPE_ID,
        'page_url': 'https://the-full-stack.com/projects',
    }
    body.update(overrides)
    return body


def api_gw_event(
    *,
    body: dict[str, Any] | None = None,
    raw_body: str | None = None,
    ip: str = '1.2.3.4',
    country: str = 'CL',
    user_agent: str | None = CHROME_UA,
) -> dict[str, Any]:
    """Construye un evento API Gateway REST proxy para POST /track.

    Si `raw_body` se pasa, se usa tal cual (para probar JSON invalido);
    sino se serializa `body` (o `{}`). Si `user_agent` es None, el header
    User-Agent se omite del evento (request sin UA).
    """
    if raw_body is not None:
        serialized = raw_body
    elif body is not None:
        serialized = json.dumps(body)
    else:
        serialized = ''

    headers: dict[str, str] = {
        'Content-Type': 'application/json',
        'Origin': 'https://the-full-stack.com',
        'CF-Connecting-IP': ip,
        'CF-IPCountry': country,
    }
    if user_agent is not None:
        headers['User-Agent'] = user_agent

    return {
        'httpMethod': 'POST',
        'path': '/track',
        'headers': headers,
        'queryStringParameters': None,
        'pathParameters': None,
        'isBase64Encoded': False,
        'body': serialized,
        'requestContext': {
            'identity': {'sourceIp': ip},
            'requestId': 'test-request-id',
            'stage': 'dev',
        },
    }


def tracking_table() -> Any:
    """Devuelve el resource boto3 de la tabla tracking emulada por moto."""
    import boto3

    return boto3.resource('dynamodb', region_name='us-east-1').Table(
        TRACKING_TABLE_NAME
    )


def cache_table() -> Any:
    """Devuelve el resource boto3 de la tabla cache emulada por moto."""
    import boto3

    return boto3.resource('dynamodb', region_name='us-east-1').Table(
        CACHE_TABLE_NAME
    )


def scan_tracking() -> list[dict[str, Any]]:
    """Devuelve todos los items persistidos en la tabla tracking.

    La tabla queda vacia al inicio de cada test (la fixture autouse de
    moto la recrea), asi que un scan refleja exactamente lo que el
    handler escribio en esa invocacion.
    """
    return tracking_table().scan().get('Items', [])
