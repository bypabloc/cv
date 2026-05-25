"""E2E — la respuesta lleva CORS Access-Control-Allow-Origin '*'.

Given un evento API Gateway de tracking valido,
When lambda_handler lo procesa end-to-end,
Then la respuesta HTTP 204 incluye el header
  Access-Control-Allow-Origin con el valor literal '*' (navigator.
  sendBeacon en modo ping lo exige) y omite el header Vary.
"""

import pytest

from tests.integration._fixtures._builders import (
    api_gw_event,
    lambda_context,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_cors_wildcard_origin_e2e():
    import handler

    # Arrange
    event = api_gw_event(body=valid_body())

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: origin '*' literal, sin Vary (sendBeacon ping lo rechaza).
    assert response['statusCode'] == 204
    headers = response['headers']
    assert headers['Access-Control-Allow-Origin'] == '*'
    assert 'Vary' not in headers
