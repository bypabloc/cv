"""shared.lambda_kit.http_dispatch.extract_request — POST.

Given un evento API Gateway con httpMethod POST y body JSON que incluye
     operation, action y otros campos,
When se procesa con extract_request,
Then devuelve operation, action y data (con los campos restantes del body).
"""

from __future__ import annotations

import json

import pytest
from shared.lambda_kit import extract_request

pytestmark = pytest.mark.unit


def test_extract_request_post_returns_operation_action_data() -> None:
    # Arrange
    body = {
        'operation': 'contact',
        'action': 'create',
        'name': 'Pablo',
        'email': 'p@example.com',
        'message': 'Hola',
    }
    event = {
        'httpMethod': 'POST',
        'body': json.dumps(body),
    }

    # Act
    result = extract_request(event)

    # Assert
    assert result.operation == 'contact'
    assert result.action == 'create'
    assert result.data == {
        'name': 'Pablo',
        'email': 'p@example.com',
        'message': 'Hola',
    }
    assert result.method == 'POST'
