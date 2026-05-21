"""Handler — body con JSON malformado.

Given un evento API Gateway con un body que no es JSON valido,
When lambda_handler lo procesa,
Then devuelve HTTP 400 con code INVALID_JSON (error_response).
"""

import json

import pytest

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_returns_400_on_invalid_json(tracking_aws: None):
    import handler

    # Arrange
    event = api_gw_event(raw_body='{not valid json')

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 400
    assert json.loads(response['body'])['code'] == 'INVALID_JSON'
