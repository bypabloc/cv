"""Handler — encoder async devuelve 202 con page_id + session_id.

Given ASYNC_MODE=true + body /track valido,
When lambda_handler procesa el request,
Then responde HTTP 202 con un body JSON que incluye page_id (UUIDv7
     pre-generado por el encoder), session_id (preservado del cliente),
     created_at (timestamp del encoder) y accepted=true.

AC-6 del plan lambdas-async-sqs.
"""

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
    captured_queue: list[dict],
    neon_off: dict[str, int],
    tracking_aws: None,
) -> None:
    import handler

    # Arrange
    event = api_gw_event(
        body=valid_body(
            page_title='Projects',
            utm_source='twitter',
            viewport_width=1920,
            niche='fintech',
        )
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: HTTP 202 con body JSON.
    assert response['statusCode'] == 202
    body = json.loads(response['body'])
    # status del encoder en modo async.
    assert body['status'] == 'accepted'
    # session_id viaja tal cual desde el cliente.
    assert body['session_id'] == SESSION_ID
    assert body['accepted'] is True
    # page_id es un UUIDv7 (36 chars con guiones y prefijo de version 7).
    assert len(body['page_id']) == 36
    assert body['page_id'][14] == '7'
    # created_at es ISO 8601 con timezone UTC.
    assert body['created_at'].endswith('+00:00') or body['created_at'].endswith(
        'Z'
    )
    # El encoder publico 1 mensaje a SQS.
    assert len(captured_queue) == 1
    # El encoder NO toco Neon.
    assert neon_off == {
        'db_session': 0,
        'ensure_session_and_visit': 0,
        'insert': 0,
    }
