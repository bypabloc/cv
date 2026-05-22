"""E2E — body con JSON malformado se rechaza sin persistir.

Given un evento API Gateway cuyo body no es JSON valido,
When lambda_handler lo procesa end-to-end,
Then devuelve HTTP 400 con code INVALID_JSON y NO persiste ningun item.
"""

import json

import pytest

from tests.integration._fixtures._builders import (
    api_gw_event,
    lambda_context,
    scan_tracking,
)

pytestmark = pytest.mark.integration


def test_malformed_json_rejected_e2e():
    import handler

    # Arrange
    event = api_gw_event(raw_body='{not valid json')

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: error HTTP 400 con el code de JSON invalido.
    assert response['statusCode'] == 400
    assert json.loads(response['body'])['code'] == 'INVALID_JSON'

    # Assert: nada se persistio.
    assert scan_tracking() == []
