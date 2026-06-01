"""Encoder devuelve error si el invoke a tracking_writer falla.

Given ASYNC_MODE=true + invoke_async lanza LambdaInvokeError,
When el handler procesa un evento valido,
Then la respuesta es 502 (el http_handler traduce el fallo del invoke
     downstream a Bad Gateway) — el cliente reintentara.
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_invoke_failure_returns_error(
    async_mode: None,
    tracking_aws: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import handler
    import services.tracking_service as svc
    from shared.aws.lambda_invoke import LambdaInvokeError

    def _boom(*, function_name: str, payload: dict) -> None:
        msg = 'lambda invoke down'
        raise LambdaInvokeError(msg)

    monkeypatch.setattr(svc, 'invoke_async', _boom)

    # Act
    response = handler.lambda_handler(
        api_gw_event(body=valid_body()), lambda_context()
    )

    # Assert: 502 (no degradacion silenciosa a 202).
    assert response['statusCode'] == 502
