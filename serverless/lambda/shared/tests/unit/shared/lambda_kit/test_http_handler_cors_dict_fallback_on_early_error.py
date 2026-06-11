"""shared.lambda_kit.http_dispatch.http_handler — fallback CORS dict.

Given un http_handler con cors_origin dict ({'cv': 'public', '*': 'echo'})
     y un request SIN operation (falla en extract_request, antes de
     conocer la operation),
When se invoca http_handler,
Then responde 400 con el modo CORS del fallback '*' (echo del Origin
     whitelisteado), no con el modo de ninguna operation.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.http_dispatch import http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    make_fake_controller,
    with_registered_controller,
)

pytestmark = pytest.mark.unit


def test_http_handler_cors_dict_fallback_on_early_error(monkeypatch) -> None:
    # Arrange
    origin_header = 'https://the-full-stack.com'
    monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
    monkeypatch.setenv('STAGE', 'prod')

    event_model, patcher = with_registered_controller(
        'cv', 'get', make_fake_controller()
    )
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {'action': 'get'},
        'headers': {'origin': origin_header},
        'requestContext': {'identity': {'sourceIp': '203.0.113.42'}},
    }

    # Act
    with patcher:
        response = http_handler(
            event,
            event_model=event_model,
            cors_origin={'cv': 'public', '*': 'echo'},
        )

    # Assert
    assert response['statusCode'] == 400
    assert (
        response['headers']['Access-Control-Allow-Origin'] == origin_header
    )
