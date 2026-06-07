"""shared.lambda_kit.http_dispatch — GET sin redirect_url -> JSON (regresion).

Given un controller GET normal que NO devuelve `redirect_url` (ej. cv.get),
When http_handler procesa el request GET,
Then responde 200 JSON normal (NO 302).

Cubre que los endpoints GET legitimos (cv) NO se ven afectados por la
logica del 302 del magic-link: solo redirige cuando hay redirect_url.
"""

from __future__ import annotations

import json

import pytest
from shared.lambda_kit.base_controller import BaseController
from shared.lambda_kit.http_dispatch import http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    _FakeModel,
    with_registered_controller,
)

pytestmark = pytest.mark.unit


class _CvController(BaseController):
    event_model = _FakeModel

    def execute(self) -> dict:
        return {
            'is_valid': True,
            'code': 0,
            'data': {'profile': {'name': 'Pablo'}},
        }


def test_http_handler_get_without_redirect_url_returns_json() -> None:
    # Arrange
    event_model, patcher = with_registered_controller(
        'cv', 'get', _CvController,
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

    # Assert: 200 JSON normal, sin Location.
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body == {'profile': {'name': 'Pablo'}}
    assert 'Location' not in response['headers']
