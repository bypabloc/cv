"""Handler — exito devuelve HTTP 201 con el contact_id.

Given un evento API Gateway con un form valido y Turnstile mock success,
When lambda_handler procesa el evento,
Then devuelve HTTP 201 con el contact_id en el body y el echo CORS.
"""

import json

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_handler_returns_201_with_contact_id(
    mock_neon_writes: list[dict], contact_form_aws: None
) -> None:
    import handler

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    event = api_gw_event(
        body={
            'name': 'Pablo Contreras',
            'email': 'user@example.com',
            'message': 'Hola, me interesa colaborar contigo.',
            'cf_token': 'x' * 30,
            'niche': 'fintech',
        },
        ip='203.0.113.30',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert len(body['contact_id']) == 36
    assert (
        response['headers']['Access-Control-Allow-Origin']
        == 'https://the-full-stack.com'
    )
