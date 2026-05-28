"""shared.lambda_kit.http_dispatch — el http_handler honra `status` del controller.

Given un controller que devuelve is_valid=False con un `status` HTTP
explicito (ej. 404),
When http_handler procesa el resultado,
Then responde con ese status y el `data` del controller tal cual (sin
envolverlo en INVALID_REQUEST 400).

Cubre el contrato que permite a un controller expresar errores de negocio
con status especifico (404/409/423/429/401) sin construir una
ApplicationError. Regresion del smoke E2E del Lambda auth (login.start
EMAIL_NOT_FOUND debe ser 404, no 400).
"""

from __future__ import annotations

import json

import pytest
from shared.lambda_kit import BaseController, http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    _FakeModel,
    with_registered_controller,
)

pytestmark = pytest.mark.unit


class _NotFoundController(BaseController):
    event_model = _FakeModel

    def execute(self) -> dict:
        return {
            'is_valid': False,
            'code': 4001,
            'status': 404,
            'data': {
                'error': 'EMAIL_NOT_FOUND',
                'suggest_register': True,
                'methods': [],
            },
        }


def test_http_handler_honors_controller_status_on_business_error() -> None:
    # Arrange
    event_model, patcher = with_registered_controller(
        'login', 'start', _NotFoundController,
    )
    event = {
        'httpMethod': 'POST',
        'body': '{"operation":"login","action":"start","email":"x@y.com"}',
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

    # Assert: status del controller (404) + body = data del controller.
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body == {
        'error': 'EMAIL_NOT_FOUND',
        'suggest_register': True,
        'methods': [],
    }
