"""shared.lambda_kit.http_dispatch.http_handler — request invalido.

Given un evento GET sin el query param 'operation',
When se invoca http_handler,
Then devuelve HTTP 400 sin invocar ningun controller.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit import build_event_model, http_handler

pytestmark = pytest.mark.unit


def test_http_handler_missing_operation_returns_400() -> None:
    # Arrange
    event_model = build_event_model({'cv': {'controller': 'cv', 'arn_key': ''}})
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {'action': 'get'},  # falta operation
        'headers': {},
    }

    # Act
    response = http_handler(
        event,
        event_model=event_model,
        cors_origin='public',
    )

    # Assert
    assert response['statusCode'] == 400
