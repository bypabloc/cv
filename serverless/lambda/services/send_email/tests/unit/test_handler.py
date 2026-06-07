"""handler.lambda_handler enruta email/send y maneja invalidos.

Given el evento del invoke async,
When lambda_handler procesa,
Then enruta a send (ok), rechaza operation invalida, y mapea el error de
     negocio (kind desconocido) a status 'rejected' sin re-lanzar.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def _context():
    """Lambda context minimo para inject_lambda_context."""

    class _Ctx:
        function_name = 'send-email-test'
        memory_limit_in_mb = 256
        invoked_function_arn = (
            'arn:aws:lambda:us-east-1:123456789012:function:send-email-test'
        )
        aws_request_id = 'test-req-id'

    return _Ctx()


def test_handler_routes_email_send():
    import handler

    event = {
        'operation': 'email',
        'action': 'send',
        'data': {
            'kind': 'login-code',
            'to': ['user@example.com'],
            'data': {'code': 'X', 'expires_in_min': 15},
        },
    }
    with patch(
        'controllers.email.send.email_service.send',
        return_value='msg-9',
    ):
        result = handler.lambda_handler(event, _context())

    assert result['status'] == 'ok'
    assert result['data'] == {'message_id': 'msg-9', 'kind': 'login-code'}


def test_handler_rejects_invalid_operation():
    import handler

    result = handler.lambda_handler(
        {'operation': 'nope', 'action': 'send', 'data': {}}, _context()
    )
    assert result['status'] == 'error'


def test_handler_rejects_unknown_kind():
    import handler
    from services.email_service import EmailServiceError

    event = {
        'operation': 'email',
        'action': 'send',
        'data': {'kind': 'ghost', 'to': ['u@e.com'], 'data': {}},
    }
    # El service levanta EmailServiceError (kind inexistente); el handler lo
    # mapea a status 'rejected' + code (sin re-lanzar — es invoke async).
    with patch(
        'controllers.email.send.email_service.send',
        side_effect=EmailServiceError(
            'kind desconocido', code=1404, error_code='EMAIL_KIND_NOT_FOUND'
        ),
    ):
        result = handler.lambda_handler(event, _context())

    assert result['status'] == 'rejected'
    assert result['code'] == 1404
