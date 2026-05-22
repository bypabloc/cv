"""Integration E2E — body JSON malformado devuelve HTTP 400.

Given un evento API Gateway cuyo body no es JSON parseable,
When se invoca el `lambda_handler` end-to-end,
Then devuelve HTTP 400 con code INVALID_JSON y NO persiste ningun
     contacto en DynamoDB.
"""

import json

import pytest

from tests.integration._fixtures import (
    _api_gw_event,
    _count_contacts,
    _lambda_context,
)

pytestmark = pytest.mark.integration


def test_malformed_json_returns_400_e2e(aws_env):
    import handler

    # Arrange
    event = _api_gw_event(body='{"name": "Pablo", broken', ip='198.51.100.21')

    # Act
    response = handler.lambda_handler(event, _lambda_context())

    # Assert
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['code'] == 'INVALID_JSON'
    assert _count_contacts() == 0
