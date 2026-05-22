"""E2E — event_type_id que no es un UUID valido se rechaza sin persistir.

Given un evento API Gateway con un event_type_id de 36 chars pero que no
  es un UUID bien formado,
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


def test_malformed_event_type_id_rejected_e2e():
    import handler

    # Arrange: 36 chars (longitud valida) pero no es un UUID con guiones.
    event = api_gw_event(
        body=valid_body(
            event_type_id='zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz'
        )
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: el field_validator de UUID rechaza -> HTTP 400 INVALID_INPUT.
    assert response['statusCode'] == 400
    assert json.loads(response['body'])['code'] == 'INVALID_INPUT'

    # Assert: nada se persistio.
    assert scan_tracking() == []
