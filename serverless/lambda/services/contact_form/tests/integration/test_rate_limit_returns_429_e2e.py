"""Integration E2E — rate-limit per-IP agotado devuelve HTTP 429.

Given una rule de endpoint `/contact` con `limit=4` en una ventana de
     60s y varias requests consecutivas desde la misma IP (cada
     submission exitosa incrementa el bucket 2 veces: el check del
     rate-limit y el contador de auto-blacklist),
When se invoca el `lambda_handler` end-to-end una vez de mas,
Then las 2 primeras devuelven HTTP 201 y la 3a devuelve HTTP 429 con
     code RATE_LIMIT_EXCEEDED (sliding window weighted).
"""

import json

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.integration._fixtures import (
    _api_gw_event,
    _lambda_context,
    _put_endpoint_rule,
    _valid_body,
)

pytestmark = pytest.mark.integration


@respx.mock
def test_rate_limit_returns_429_e2e(aws_env):
    import handler

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    _put_endpoint_rule(endpoint='/contact', limit=4, window_seconds=60)
    ip = '198.51.100.26'

    def _submit() -> dict:
        return handler.lambda_handler(
            _api_gw_event(body=_valid_body(), ip=ip), _lambda_context()
        )

    # Act
    first = _submit()
    second = _submit()
    third = _submit()

    # Assert
    assert first['statusCode'] == 201
    assert second['statusCode'] == 201
    assert third['statusCode'] == 429
    body = json.loads(third['body'])
    assert body['code'] == 'RATE_LIMIT_EXCEEDED'
