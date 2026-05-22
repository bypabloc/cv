"""E2E — payload sin session_id se rechaza sin persistir.

Given un evento API Gateway cuyo body no incluye session_id,
When lambda_handler lo procesa end-to-end,
Then devuelve HTTP 400 con code INVALID_INPUT y NO persiste ningun item.
"""

import json

import pytest

from tests.integration._fixtures._builders import (
    api_gw_event,
    lambda_context,
    scan_tracking,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_missing_session_id_rejected_e2e():
    import handler

    # Arrange: body valido menos session_id.
    body = valid_body()
    del body['session_id']
    event = api_gw_event(body=body)

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: el modelo Pydantic rechaza -> HTTP 400 INVALID_INPUT.
    assert response['statusCode'] == 400
    assert json.loads(response['body'])['code'] == 'INVALID_INPUT'

    # Assert: nada se persistio.
    assert scan_tracking() == []
