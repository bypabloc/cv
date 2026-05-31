"""Handler async (ASYNC_MODE=true) devuelve 202 con page_id en el body.

Given ASYNC_MODE=true,
When el handler procesa un evento de tracking valido,
Then la respuesta es 202 con `page_id` (UUIDv7) y `session_id` en el
     body JSON, y se invoco tracking_writer exactamente una vez.
"""

from __future__ import annotations

import json

import pytest

from tests.unit._helpers import (
    SESSION_ID,
    api_gw_event,
    lambda_context,
    valid_body,
)

pytestmark = pytest.mark.unit


def test_handler_returns_202_with_page_id_in_async_mode(
    async_mode: None,
    captured_invoke: list[dict],
    tracking_aws: None,
) -> None:
    import handler

    # Act
    response = handler.lambda_handler(
        api_gw_event(body=valid_body()), lambda_context()
    )

    # Assert
    assert response['statusCode'] == 202
    body = json.loads(response['body'])
    assert 'page_id' in body
    assert body['session_id'] == SESSION_ID
    assert len(captured_invoke) == 1
