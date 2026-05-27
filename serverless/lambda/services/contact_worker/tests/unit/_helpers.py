"""Builders compartidos para los tests unit del Lambda `contact_worker`.

Prefijo `_` para que pytest NO recolecte este archivo como tests.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

# UUIDv7 valido determinista para los tests (version=7 en pos 14).
_DEFAULT_CONTACT_ID = '019e5c50-0000-7000-8000-000000000001'
_DEFAULT_SESSION_ID = 'cf-019e5c50-0000-7000-8000-000000000099'
_DEFAULT_MESSAGE_ID = '019e5c50-0000-7000-8000-msg00000001'
_DEFAULT_CREATED_AT = '2026-05-25T18:00:00+00:00'


def lambda_context() -> MagicMock:
    """Devuelve un Lambda context falso valido para Powertools.

    `logger.inject_lambda_context` lee `function_name`,
    `memory_limit_in_mb`, `invoked_function_arn` y `aws_request_id` del
    context.
    """
    ctx = MagicMock()
    ctx.function_name = 'portfolio-contact-worker-test'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:'
        'portfolio-contact-worker-test'
    )
    ctx.aws_request_id = 'test-request-id'
    ctx.get_remaining_time_in_millis = lambda: 30000
    return ctx


def message_body(
    *,
    contact_id: str = _DEFAULT_CONTACT_ID,
    session_id: str = _DEFAULT_SESSION_ID,
    created_at: str = _DEFAULT_CREATED_AT,
    name: str = 'Pablo Contreras',
    email: str = 'user@example.com',
    message: str = 'Hola mundo largo de prueba para el worker',
    niche: str | None = 'fintech',
    **overrides: Any,
) -> dict[str, Any]:
    """Construye el dict del body de un mensaje SQS valido.

    Refleja el contrato `ContactQueueMessage`. Los `overrides` permiten
    sobreescribir cualquier campo individual sin recrear el dict entero.
    """
    body: dict[str, Any] = {
        'schema_version': 1,
        'contact_id': contact_id,
        'created_at': created_at,
        'session_id': session_id,
        'name': name,
        'email': email,
        'message': message,
        'company': None,
        'role': None,
        'service_type': None,
        'budget': None,
        'timeline': None,
        'niche': niche,
        'ip': '203.0.113.10',
        'country': 'CL',
        'user_agent': 'Mozilla/5.0',
        'origin_niche': niche,
    }
    body.update(overrides)
    return body


def sqs_record(
    *,
    message_id: str = _DEFAULT_MESSAGE_ID,
    body: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    """Construye un record SQS con `body` serializado a JSON."""
    if body is None:
        body = message_body()
    body_str = body if isinstance(body, str) else json.dumps(body)
    return {
        'messageId': message_id,
        'receiptHandle': f'AQEBfake-{message_id}',
        'body': body_str,
        'attributes': {
            'ApproximateReceiveCount': '1',
            'SentTimestamp': '1716660000000',
            'SenderId': 'AIDAFAKE',
            'ApproximateFirstReceiveTimestamp': '1716660001000',
        },
        'messageAttributes': {},
        'md5OfBody': '00000000000000000000000000000000',
        'eventSource': 'aws:sqs',
        'eventSourceARN': (
            'arn:aws:sqs:us-east-1:000000000000:portfolio-contact-form-test'
        ),
        'awsRegion': 'us-east-1',
    }


def sqs_event(
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Construye un evento SQS valido (lista de records).

    Si `records` es None, crea un batch con un solo record default.
    """
    return {'Records': records if records is not None else [sqs_record()]}
