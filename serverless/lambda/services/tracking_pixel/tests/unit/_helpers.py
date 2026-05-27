"""Builders compartidos para los tests unit del Lambda `tracking_pixel`.

Prefijo `_` para que pytest NO recolecte este archivo como tests.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

# Body de tracking valido reutilizable: session_id de 28 chars, event_id
# de 32 chars (UUID sin guiones), event_type_id de 36 chars (UUID con
# guiones). Todos cumplen los limites de TrackEventModel.
SESSION_ID = 'session-uuid-1234567890abcdef'
EVENT_ID = 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
EVENT_TYPE_ID = '019e372b-e0a7-7154-8279-8829bcf6a08c'
CHROME_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    'Chrome/118.0.0.0 Safari/537.36'
)


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
    """Devuelve un body de tracking valido (todos los required + overrides).

    Spec tracking-data-completeness: page_path/page_url/page_title +
    viewport_* + utm_* son required. Defaults realistas para los tests
    no enfocados en validacion del modelo.
    """
    body: dict[str, Any] = {
        'session_id': SESSION_ID,
        'event_id': EVENT_ID,
        'event_type_id': EVENT_TYPE_ID,
        'page_url': 'https://the-full-stack.com/projects',
        'page_path': '/projects',
        'page_title': 'Projects',
        'viewport_width': 1280,
        'viewport_height': 800,
        'utm_source': '',
        'utm_medium': '',
        'utm_campaign': '',
        'utm_content': '',
    }
    body.update(overrides)
    return body


def api_gw_event(
    *,
    body: dict[str, Any] | None = None,
    raw_body: str | None = None,
    ip: str = '1.2.3.4',
    country: str = 'CL',
    user_agent: str = CHROME_UA,
) -> dict[str, Any]:
    """Construye un evento API Gateway REST proxy para POST /track.

    Si `raw_body` se pasa, se usa tal cual (para probar JSON invalido);
    sino se serializa `body` (o `{}`).
    """
    if raw_body is not None:
        serialized = raw_body
    elif body is not None:
        # El contrato HTTP del backend exige operation y action en el body
        # (resueltos por shared.lambda_kit.http_handler). Los tests viejos
        # solo enviaban los campos de tracking; aqui se inyectan los
        # defaults si no estan, manteniendo los tests focales.
        body = {'operation': 'tracking', 'action': 'track', **body}
        serialized = json.dumps(body)
    else:
        serialized = ''

    return {
        'httpMethod': 'POST',
        'path': '/track',
        'headers': {
            'Content-Type': 'application/json',
            'Origin': 'https://the-full-stack.com',
            'CF-Connecting-IP': ip,
            'CF-IPCountry': country,
            'User-Agent': user_agent,
        },
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
