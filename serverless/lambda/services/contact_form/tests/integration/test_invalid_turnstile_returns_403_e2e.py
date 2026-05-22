"""Integration E2E — Turnstile invalido devuelve HTTP 403.

Given un evento API Gateway con un form valido pero Cloudflare
     siteverify responde success=false,
When se invoca el `lambda_handler` end-to-end,
Then devuelve HTTP 403 con code CAPTCHA_INVALID y NO persiste contacto.
"""

import json

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.integration._fixtures import (
    _api_gw_event,
    _count_contacts,
    _lambda_context,
    _valid_body,
)

pytestmark = pytest.mark.integration


@respx.mock
def test_invalid_turnstile_returns_403_e2e(aws_env):
    import handler

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200,
            json={'success': False, 'error-codes': ['invalid-input-response']},
        )
    )
    event = _api_gw_event(body=_valid_body(), ip='198.51.100.25')

    # Act
    response = handler.lambda_handler(event, _lambda_context())

    # Assert
    assert response['statusCode'] == 403
    body = json.loads(response['body'])
    assert body['code'] == 'CAPTCHA_INVALID'
    assert _count_contacts() == 0
