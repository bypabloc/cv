"""Rate-limit excedido NO invoca a tracking_writer (corre antes del branch).

Given ASYNC_MODE=true + IP rate-limited,
When el handler procesa el evento,
Then responde 429 Y NUNCA se invoca tracking_writer (rate-limit corre
     ANTES del branch async).
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_rate_limit_failure_does_not_invoke(
    async_mode: None,
    captured_invoke: list[dict],
    tracking_aws: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import controllers.tracking.track as track_mod
    import handler
    from shared.rate_limit.exceptions import RateLimitExceededError

    # Arrange: forzar rate-limit (mock check_or_raise -> raise).
    def _reject(**_kwargs):
        msg = 'rate limit'
        raise RateLimitExceededError(msg, code='RATE_LIMITED')

    monkeypatch.setattr(track_mod, 'check_or_raise', _reject)

    # Act
    response = handler.lambda_handler(
        api_gw_event(body=valid_body()), lambda_context()
    )

    # Assert
    assert response['statusCode'] == 429
    assert len(captured_invoke) == 0
