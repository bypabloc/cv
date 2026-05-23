"""shared.lambda_kit.http_dispatch.http_handler — ApplicationError.

Given un controller que levanta una ApplicationError de negocio,
When http_handler la procesa,
Then la traduce a una respuesta HTTP de error (status acorde al exc).
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import RateLimitExceededError
from shared.lambda_kit import BaseController, http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    _FakeModel,
    with_registered_controller,
)

pytestmark = pytest.mark.unit


class _RateLimitController(BaseController):
    event_model = _FakeModel

    def execute(self) -> dict:
        raise RateLimitExceededError(
            'too many requests',
            code='RATE_LIMITED',
        )


def test_http_handler_application_error_maps_to_http() -> None:
    # Arrange
    event_model, patcher = with_registered_controller(
        'contact', 'create', _RateLimitController
    )
    event = {
        'httpMethod': 'POST',
        'body': '{"operation":"contact","action":"create","name":"x"}',
        'headers': {'origin': 'https://the-full-stack.com'},
    }

    # Act
    with patcher:
        response = http_handler(
            event,
            event_model=event_model,
            cors_origin='echo',
            success_status=201,
        )

    # Assert
    assert response['statusCode'] == 429
