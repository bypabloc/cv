"""Builders compartidos para los tests unit del Lambda `tracking_writer`.

Prefijo `_` para que pytest NO recolecte este archivo como tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

# Defaults realistas para los tests no enfocados en validacion del
# modelo. `session_id` corto pero unico, `event_id` UUIDv4 sin guiones
# (32 chars) y `event_type_id` UUID con guiones (36 chars).
SESSION_ID = 'session-uuid-1234567890abcdef'
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
    ctx.function_name = 'portfolio-tracking-writer-test'
    ctx.memory_limit_in_mb = 256
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:'
        'portfolio-tracking-writer-test'
    )
    ctx.aws_request_id = 'test-request-id'
    ctx.get_remaining_time_in_millis = lambda: 30000
    return ctx


def valid_body(index: int = 0, **overrides: Any) -> dict[str, Any]:
    """Devuelve el `data` (mensaje) de un evento de tracking valido.

    `index` distingue eventos (page_id, event_id, created_at varian).
    """
    body: dict[str, Any] = {
        'schema_version': 1,
        'page_id': f'019e5c50-0000-7000-8000-{index:012d}',
        'created_at': f'2026-05-25T12:00:{index:02d}+00:00',
        'session_id': SESSION_ID,
        'event_id': f'a1b2c3d4e5f60718293a4b5c6d7e8f9{index:01x}'.ljust(
            32,
            '0',
        )[:32],
        'event_type_id': EVENT_TYPE_ID,
        'page_path': f'/projects?n={index}',
        'niche': 'fintech',
        'viewport_width': 1920,
        'viewport_height': 1080,
        'event_props': None,
        'utm_source': None,
        'utm_medium': None,
        'utm_campaign': None,
        'utm_content': None,
        'utm_term': None,
        'referrer': None,
        'ip': '1.2.3.4',
        'country': 'CL',
        'user_agent': CHROME_UA,
    }
    body.update(overrides)
    return body


def write_event(index: int = 0, **overrides: Any) -> dict[str, Any]:
    """Construye el evento del invoke async `{operation, action, data}`.

    El encoder `tracking_pixel` invoca al writer con este contrato. El
    `data` es el mensaje de tracking (ver `valid_body`).
    """
    return {
        'operation': 'tracking',
        'action': 'write',
        'data': valid_body(index, **overrides),
    }
