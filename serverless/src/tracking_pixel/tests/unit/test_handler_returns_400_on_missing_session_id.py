"""Handler — body sin session_id.

Given un evento API Gateway con un body al que le falta session_id,
When lambda_handler lo procesa,
Then devuelve HTTP 400 (la fase validate del controller rechaza el body).
"""

import json

import pytest

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_returns_400_on_missing_session_id(tracking_aws: None):
    import handler

    # Arrange: body sin session_id (campo requerido del modelo).
    event = api_gw_event(
        body={
            'event_id': 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
            'event_type_id': '019e372b-e0a7-7154-8279-8829bcf6a08c',
            'page_url': 'https://the-full-stack.com/',
        }
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 400
    assert json.loads(response['body'])['code'] == 'INVALID_INPUT'
