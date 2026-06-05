"""Controller email/send normaliza exito y error de negocio.

Given un EmailSendRequest valido (el controller recibe solo el `data`,
no el evento completo: run_controller pasa controller_event=data),
When se ejecuta el controller Send,
Then normaliza el resultado del service a {is_valid, data, code}.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_send_controller_normalizes_success():
    from controllers.email.send import Send

    # El controller recibe el `data` (no {operation,action,data}).
    data = {
        'kind': 'login-code',
        'to': ['user@example.com'],
        'data': {'code': 'X', 'expires_in_min': 15},
    }
    controller = Send(event=data)
    with patch(
        'controllers.email.send.email_service.send',
        return_value='msg-42',
    ) as mock_send:
        result = controller.run()

    assert result == {
        'is_valid': True,
        'data': {'message_id': 'msg-42', 'kind': 'login-code'},
        'code': 0,
    }
    mock_send.assert_called_once_with(
        kind='login-code',
        to=['user@example.com'],
        data={'code': 'X', 'expires_in_min': 15},
        reply_to=None,
    )


def test_send_controller_maps_service_error():
    from controllers.email.send import Send
    from services.email_service import EmailServiceError

    data = {'kind': 'bad', 'to': ['u@e.com'], 'data': {}}
    controller = Send(event=data)
    with patch(
        'controllers.email.send.email_service.send',
        side_effect=EmailServiceError(
            'kind desconocido', code=1404, error_code='EMAIL_KIND_NOT_FOUND'
        ),
    ):
        result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 1404
    assert result['data']['error_code'] == 'EMAIL_KIND_NOT_FOUND'
