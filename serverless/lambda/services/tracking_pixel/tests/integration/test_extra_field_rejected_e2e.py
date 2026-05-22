"""E2E — campo no declarado en el body se rechaza sin persistir.

Given un evento API Gateway cuyo body incluye un campo extra que
  TrackEventModel no declara (model_config extra='forbid'),
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


def test_extra_field_rejected_e2e():
    import handler

    # Arrange: body valido + un campo no declarado en el modelo.
    event = api_gw_event(
        body=valid_body(unexpected_field='inyeccion')
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: extra='forbid' rechaza el campo -> HTTP 400 INVALID_INPUT.
    assert response['statusCode'] == 400
    assert json.loads(response['body'])['code'] == 'INVALID_INPUT'

    # Assert: nada se persistio.
    assert scan_tracking() == []
