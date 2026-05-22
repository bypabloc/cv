"""Integration E2E — CORS no refleja un origin fuera de la whitelist.

Given un evento API Gateway con un `Origin` que NO esta en la whitelist
     CORS (un dominio arbitrario),
When se invoca el `lambda_handler` end-to-end con un body invalido,
Then la respuesta de error NO refleja el origin del atacante: el header
     `Access-Control-Allow-Origin` cae al apex `the-full-stack.com`.
"""

import json

import pytest

from tests.integration._fixtures import _api_gw_event, _lambda_context

pytestmark = pytest.mark.integration


def test_cors_rejects_unknown_origin_e2e(aws_env):
    import handler

    # Arrange: body invalido (JSON roto) + origin no whitelisteado.
    event = _api_gw_event(
        body='{roto',
        ip='198.51.100.31',
        origin='https://evil.example.com',
    )

    # Act
    response = handler.lambda_handler(event, _lambda_context())

    # Assert
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['code'] == 'INVALID_JSON'
    assert (
        response['headers']['Access-Control-Allow-Origin']
        == 'https://the-full-stack.com'
    )
