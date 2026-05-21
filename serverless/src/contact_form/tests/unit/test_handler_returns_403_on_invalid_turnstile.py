"""Handler — Turnstile invalido devuelve HTTP 403.

Given un evento API Gateway con un form valido pero Turnstile responde
     success=false,
When lambda_handler procesa el evento,
Then devuelve HTTP 403 con code CAPTCHA_INVALID (error_response).
"""

import json

import httpx
import pytest
import respx

from shared.turnstile import TURNSTILE_SITEVERIFY_URL
from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_handler_returns_403_on_invalid_turnstile(contact_form_aws):
    import handler

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200,
            json={'success': False, 'error-codes': ['timeout-or-duplicate']},
        )
    )
    event = api_gw_event(
        body={
            'name': 'Pablo Contreras',
            'email': 'user@example.com',
            'message': 'Hola, me interesa colaborar contigo.',
            'cf_token': 'x' * 30,
        },
        ip='203.0.113.33',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 403
    body = json.loads(response['body'])
    assert body['code'] == 'CAPTCHA_INVALID'
