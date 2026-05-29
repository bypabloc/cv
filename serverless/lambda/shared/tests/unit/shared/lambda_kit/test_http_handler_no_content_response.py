"""shared.lambda_kit.http_dispatch.http_handler — 204 No Content.

Given un controller que devuelve exito y success_status=204,
When http_handler responde,
Then devuelve HTTP 204 sin body (no_content_response).
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.http_dispatch import http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    make_fake_controller,
    with_registered_controller,
)

pytestmark = pytest.mark.unit


def test_http_handler_no_content_response() -> None:
    # Arrange
    controller_cls = make_fake_controller()
    event_model, patcher = with_registered_controller(
        'tracking', 'track', controller_cls
    )
    event = {
        'httpMethod': 'POST',
        'body': '{"operation":"tracking","action":"track","ev":"pageview"}',
        'headers': {'origin': 'https://the-full-stack.com'},
    }

    # Act
    with patcher:
        response = http_handler(
            event,
            event_model=event_model,
            cors_origin='public',
            success_status=204,
        )

    # Assert
    assert response['statusCode'] == 204
    # no_content_response omite el body o lo deja como string vacio.
    assert response.get('body', '') in ('', None)
