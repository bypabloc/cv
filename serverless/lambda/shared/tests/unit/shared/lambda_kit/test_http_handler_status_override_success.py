"""shared.lambda_kit.http_dispatch — `status` override en exito (204).

Given un controller que devuelve is_valid=True con status=204,
When http_handler lo procesa (con success_status=200 por default),
Then responde 204 sin body (no_content_response).

Cubre session.logout, que cierra sesion y debe responder 204 aunque el
handler del Lambda auth use success_status=200 para el resto de actions.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_controller import BaseController
from shared.lambda_kit.http_dispatch import http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    _FakeModel,
    with_registered_controller,
)

pytestmark = pytest.mark.unit


class _LogoutController(BaseController):
    event_model = _FakeModel

    def execute(self) -> dict:
        return {'is_valid': True, 'code': 0, 'status': 204, 'data': {}}


def test_http_handler_status_override_returns_204_no_body() -> None:
    # Arrange
    event_model, patcher = with_registered_controller(
        'session', 'logout', _LogoutController,
    )
    event = {
        'httpMethod': 'POST',
        'body': '{"operation":"session","action":"logout","access_token":"x"}',
        'headers': {'origin': 'https://the-full-stack.com'},
    }

    # Act
    with patcher:
        response = http_handler(
            event,
            event_model=event_model,
            cors_origin='echo',
            success_status=200,
        )

    # Assert: 204 (override del controller) + body vacio.
    assert response['statusCode'] == 204
    assert response['body'] == ''
