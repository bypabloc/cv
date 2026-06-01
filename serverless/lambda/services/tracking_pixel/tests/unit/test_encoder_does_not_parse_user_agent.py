"""Encoder async NO parsea el User-Agent (lo hace el writer, cacheado).

Given ASYNC_MODE=true,
When el handler procesa un evento,
Then `parse_user_agent` NUNCA se invoca en el encoder (el writer lo
     hace, con cache compartido).
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_encoder_does_not_parse_user_agent(
    async_mode: None,
    captured_invoke: list[dict],
    tracking_aws: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import handler
    import services.tracking_service as svc

    called = {'n': 0}

    def _spy_parse(_ua):
        called['n'] += 1
        return {
            'browser': 'x',
            'browser_version': '1',
            'os': 'y',
            'device_type': 'desktop',
        }

    monkeypatch.setattr(svc, 'parse_user_agent', _spy_parse)

    # Act
    handler.lambda_handler(api_gw_event(body=valid_body()), lambda_context())

    # Assert: el encoder NO parsea UA.
    assert called['n'] == 0
