"""shared.lambda_kit.http_dispatch.http_handler — CORS dict por operation.

Given un http_handler con cors_origin dict ({'cv': 'public', '*': 'echo'})
     y dos requests del mismo Lambda: uno a la operation 'cv' (publica) y
     otro a la operation 'content' (admin, echo del Origin whitelisteado),
When se invoca http_handler para cada uno,
Then la respuesta de 'cv' lleva Access-Control-Allow-Origin '*' y la de
     'content' ECHOA el Origin del request.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.http_dispatch import http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    make_fake_controller,
    with_registered_controller,
)

pytestmark = pytest.mark.unit

_CORS_BY_OPERATION = {'cv': 'public', '*': 'echo'}


def test_http_handler_cors_dict_by_operation(monkeypatch) -> None:
    # Arrange
    origin_header = 'https://the-full-stack.com'
    monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
    monkeypatch.setenv('STAGE', 'prod')

    controller = make_fake_controller()
    public_model, public_patcher = with_registered_controller(
        'cv', 'get', controller
    )
    admin_model, admin_patcher = with_registered_controller(
        'content', 'get-all', controller
    )

    public_event = {
        'httpMethod': 'GET',
        'queryStringParameters': {'operation': 'cv', 'action': 'get'},
        'headers': {'origin': origin_header},
        'requestContext': {'identity': {'sourceIp': '203.0.113.42'}},
    }
    admin_event = {
        'httpMethod': 'POST',
        'body': '{"operation": "content", "action": "get-all"}',
        'headers': {'origin': origin_header},
        'requestContext': {'identity': {'sourceIp': '203.0.113.42'}},
    }

    # Act
    with public_patcher:
        public_response = http_handler(
            public_event,
            event_model=public_model,
            cors_origin=_CORS_BY_OPERATION,
        )
    with admin_patcher:
        admin_response = http_handler(
            admin_event,
            event_model=admin_model,
            cors_origin=_CORS_BY_OPERATION,
        )

    # Assert
    assert public_response['statusCode'] == 200
    assert (
        public_response['headers']['Access-Control-Allow-Origin'] == '*'
    )
    assert admin_response['statusCode'] == 200
    assert (
        admin_response['headers']['Access-Control-Allow-Origin']
        == origin_header
    )
