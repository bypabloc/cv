"""Payload del invoke a tracking_writer es JSON-serializable.

Given ASYNC_MODE=true,
When el encoder arma el payload del invoke,
Then es 100% JSON-serializable: json.dumps no lanza, y round-trips a un
     dict identico. El mensaje del evento viaja en `payload['data']`.
"""

from __future__ import annotations

import json

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_message_payload_is_serializable_json(
    async_mode: None,
    captured_invoke: list[dict],
    tracking_aws: None,
) -> None:
    import handler

    # Act
    handler.lambda_handler(api_gw_event(body=valid_body()), lambda_context())

    # Assert: exactamente un invoke, payload JSON-serializable.
    assert len(captured_invoke) == 1
    payload = captured_invoke[0]['payload']
    assert payload['operation'] == 'tracking'
    assert payload['action'] == 'write'
    serialized = json.dumps(payload)
    assert json.loads(serialized) == payload
