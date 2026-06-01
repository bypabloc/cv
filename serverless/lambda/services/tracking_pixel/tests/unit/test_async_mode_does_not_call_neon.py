"""Encoder async (ASYNC_MODE=true) NO toca Neon.

Given ASYNC_MODE=true,
When el handler procesa un evento de tracking valido,
Then NO se abre db_session, NO se llama ensure_session_and_visit ni
     insert_tracking (el writer hace la persistencia, no el encoder),
     se invoca tracking_writer una vez, y la respuesta es 202.
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_async_mode_does_not_call_neon(
    async_mode: None,
    neon_off: dict[str, int],
    captured_invoke: list[dict],
    tracking_aws: None,
) -> None:
    import handler

    # Act
    response = handler.lambda_handler(
        api_gw_event(body=valid_body()), lambda_context()
    )

    # Assert: respondio 202 sin tocar Neon; invoco tracking_writer 1 vez.
    assert response['statusCode'] == 202
    assert neon_off['db_session'] == 0
    assert neon_off['ensure_session_and_visit'] == 0
    assert neon_off['insert'] == 0
    assert len(captured_invoke) == 1
