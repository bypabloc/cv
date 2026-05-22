"""Builders compartidos para los tests unit del Lambda `stream_processor`.

Prefijo `_` para que pytest NO recolecte este archivo como tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

_CONTACTS_ARN = (
    'arn:aws:dynamodb:us-east-1:123:table/portfolio-contacts-dev/stream/x'
)
_TRACKING_ARN = (
    'arn:aws:dynamodb:us-east-1:123:table/portfolio-tracking-dev/stream/x'
)


def lambda_context() -> MagicMock:
    """Devuelve un Lambda context falso valido para Powertools.

    `logger.inject_lambda_context` lee `function_name`,
    `memory_limit_in_mb`, `invoked_function_arn` y `aws_request_id`.
    """
    ctx = MagicMock()
    ctx.function_name = 'portfolio-stream-processor-test'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:'
        'portfolio-stream-processor-test'
    )
    ctx.aws_request_id = 'test-request-id'
    return ctx


def contact_record(event_id: str) -> dict[str, Any]:
    """Construye un Stream record INSERT de la tabla `contacts`."""
    return {
        'eventID': event_id,
        'eventName': 'INSERT',
        'eventSourceARN': _CONTACTS_ARN,
        'dynamodb': {
            'NewImage': {
                'id': {'S': f'contact-{event_id}'},
                'name': {'S': 'Pablo'},
                'email': {'S': 'p@example.com'},
                'message': {'S': 'hola'},
                'created_at': {'S': '2026-05-17T00:00:00Z'},
            },
        },
    }


def tracking_record(event_id: str) -> dict[str, Any]:
    """Construye un Stream record INSERT de la tabla `tracking`."""
    return {
        'eventID': event_id,
        'eventName': 'INSERT',
        'eventSourceARN': _TRACKING_ARN,
        'dynamodb': {
            'NewImage': {
                'session_id': {'S': f'sess-{event_id}'},
                'page_id': {'S': '019e372b-e0a7-7154-8279-8829bcf6a08c'},
                'page_url': {'S': 'https://the-full-stack.com/'},
                'created_at': {'S': '2026-05-17T00:00:00Z'},
            },
        },
    }


def stream_event(*records: dict[str, Any]) -> dict[str, Any]:
    """Construye el evento DynamoDB Stream `{Records: [...]}`."""
    return {'Records': list(records)}
