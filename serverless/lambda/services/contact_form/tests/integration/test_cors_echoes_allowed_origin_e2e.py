"""Integration E2E — CORS refleja el origin permitido en la respuesta.

Given un evento API Gateway con un `Origin` que esta en la whitelist
     CORS (un subdominio niche del portfolio),
When se invoca el `lambda_handler` end-to-end con un form valido,
Then la respuesta HTTP 201 lleva ese mismo origin en el header
     `Access-Control-Allow-Origin` (echo, no comodin).
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.integration._fixtures import (
    _api_gw_event,
    _lambda_context,
    _valid_body,
)

pytestmark = pytest.mark.integration


@respx.mock
def test_cors_echoes_allowed_origin_e2e(aws_env):
    import handler

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    allowed_origin = 'https://fintech.portfolio.the-full-stack.com'
    event = _api_gw_event(
        body=_valid_body(),
        ip='198.51.100.30',
        origin=allowed_origin,
    )

    # Act
    response = handler.lambda_handler(event, _lambda_context())

    # Assert
    assert response['statusCode'] == 201
    assert (
        response['headers']['Access-Control-Allow-Origin'] == allowed_origin
    )
    assert response['headers']['Vary'] == 'Origin'
