"""E2E — event_id que no es un UUID valido se rechaza sin persistir.

Given un evento API Gateway con un event_id de longitud valida pero que
  no es un UUID bien formado,
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


def test_malformed_event_id_rejected_e2e():
    import handler

    # Arrange: 32 chars (longitud valida) pero no es un UUID hex valido.
    event = api_gw_event(
        body=valid_body(event_id='zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz')
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: el field_validator de UUID rechaza -> HTTP 400 INVALID_INPUT.
    assert response['statusCode'] == 400
    assert json.loads(response['body'])['code'] == 'INVALID_INPUT'

    # Assert: nada se persistio.
    assert scan_tracking() == []
