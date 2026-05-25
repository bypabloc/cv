"""E2E — superar 30 requests/min desde la misma IP dispara rate-limit.

Given la regla de endpoint /track con limit=30 por ventana de 60s,
When lambda_handler procesa 31 requests desde la misma IP en la misma
  ventana,
Then las primeras 30 devuelven HTTP 204 y la request 31 devuelve HTTP
  429 con code RATE_LIMIT_EXCEEDED.
"""

import json

import pytest

from tests.integration._fixtures._builders import (
    api_gw_event,
    lambda_context,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_rate_limit_exceeded_e2e():
    import handler

    # Arrange: 31 requests desde la misma IP al endpoint /track (limit 30).
    ip = '203.0.113.7'
    ctx = lambda_context()

    # Act: las primeras 30 requests caen dentro del limite.
    statuses = [
        handler.lambda_handler(
            api_gw_event(body=valid_body(), ip=ip), ctx
        )['statusCode']
        for _ in range(30)
    ]
    # La request 31 supera el limite del sliding window.
    over_limit = handler.lambda_handler(
        api_gw_event(body=valid_body(), ip=ip), ctx
    )

    # Assert: las 30 primeras pasaron (204), la 31 fue rechazada (429).
    assert statuses == [204] * 30
    assert over_limit['statusCode'] == 429
    assert (
        json.loads(over_limit['body'])['code'] == 'RATE_LIMIT_EXCEEDED'
    )
