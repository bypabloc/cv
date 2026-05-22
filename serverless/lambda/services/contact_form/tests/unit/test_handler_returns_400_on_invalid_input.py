"""Handler — body sin campo obligatorio devuelve HTTP 400.

Given un evento API Gateway con un body JSON valido pero sin el campo
     obligatorio `name`,
When lambda_handler procesa el evento,
Then devuelve HTTP 400 con code INVALID_INPUT (error_response).
"""

import json

import pytest

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_returns_400_on_invalid_input(contact_form_aws):
    import handler

    # Arrange
    event = api_gw_event(
        body={
            'email': 'user@example.com',
            'message': 'Mensaje de prueba sin nombre.',
            'cf_token': 'x' * 30,
        },
        ip='203.0.113.32',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['code'] == 'INVALID_INPUT'
