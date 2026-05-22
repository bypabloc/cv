"""E2E — event_props que excede 2048 bytes se rechaza sin persistir.

Given un evento API Gateway con un event_props cuyo JSON serializado
  supera el limite EVENT_PROPS_MAX_BYTES (2048 bytes),
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


def test_oversized_event_props_rejected_e2e():
    import handler

    # Arrange: un string de 3000 chars infla event_props por encima del
    # limite de 2048 bytes que valida TrackEventModel.
    event = api_gw_event(
        body=valid_body(event_props={'payload': 'x' * 3000})
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: el validador de tamano rechaza -> HTTP 400 INVALID_INPUT.
    assert response['statusCode'] == 400
    assert json.loads(response['body'])['code'] == 'INVALID_INPUT'

    # Assert: nada se persistio.
    assert scan_tracking() == []
