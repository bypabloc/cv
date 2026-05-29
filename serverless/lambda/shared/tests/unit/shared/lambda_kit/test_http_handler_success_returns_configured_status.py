"""shared.lambda_kit.http_dispatch.http_handler — exito.

Given un evento GET valido y un controller que devuelve is_valid=True,
When se invoca http_handler con success_status=200,
Then devuelve una respuesta HTTP 200 con el data del controller.
"""

from __future__ import annotations

import json

import pytest
from shared.lambda_kit.http_dispatch import http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    make_fake_controller,
    with_registered_controller,
)

pytestmark = pytest.mark.unit


def test_http_handler_success_returns_configured_status() -> None:
    # Arrange
    controller_cls = make_fake_controller(
        execute_result={'is_valid': True, 'data': {'name': 'Pablo'}, 'code': 0},
    )
    event_model, patcher = with_registered_controller(
        'cv', 'get', controller_cls
    )

    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {'operation': 'cv', 'action': 'get'},
        'headers': {'origin': 'https://the-full-stack.com'},
    }

    # Act
    with patcher:
        response = http_handler(
            event,
            event_model=event_model,
            cors_origin='public',
            success_status=200,
        )

    # Assert
    assert response['statusCode'] == 200
    assert json.loads(response['body']) == {'name': 'Pablo'}
