"""Integration E2E — message demasiado corto devuelve HTTP 400.

Given un evento API Gateway con un body JSON valido pero un `message`
     mas corto que el `min_length=10` del modelo Pydantic,
When se invoca el `lambda_handler` end-to-end,
Then devuelve HTTP 400 con code INVALID_INPUT y NO persiste contacto.
"""

import json

import pytest

from tests.integration._fixtures import (
    _api_gw_event,
    _count_contacts,
    _lambda_context,
    _valid_body,
)

pytestmark = pytest.mark.integration


def test_short_message_returns_400_e2e(aws_env):
    import handler

    # Arrange
    event = _api_gw_event(
        body=_valid_body(message='corto'),
        ip='198.51.100.23',
    )

    # Act
    response = handler.lambda_handler(event, _lambda_context())

    # Assert
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['code'] == 'INVALID_INPUT'
    assert _count_contacts() == 0
