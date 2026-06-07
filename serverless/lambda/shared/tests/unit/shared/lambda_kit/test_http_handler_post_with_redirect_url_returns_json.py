"""shared.lambda_kit.http_dispatch — POST con redirect_url -> JSON (no 302).

Given el mismo controller que devuelve `redirect_url` en data,
When http_handler procesa un request POST (body JSON),
Then responde 200 JSON con redirect_url + access_token en el body (NO 302).

Cubre que el admin (que llama verify-magic-link por fetch POST) sigue
recibiendo los tokens en JSON; solo el GET (navegacion del browser) hace
el 302.
"""

from __future__ import annotations

import json

import pytest
from shared.lambda_kit.base_controller import BaseController
from shared.lambda_kit.http_dispatch import http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    _FakeModel,
    with_registered_controller,
)

pytestmark = pytest.mark.unit

_REDIRECT = (
    'https://admin.portfolio.dev.the-full-stack.com/callback'
    '#access=acc&refresh=ref'
)


class _MagicLinkController(BaseController):
    event_model = _FakeModel

    def execute(self) -> dict:
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'redirect_url': _REDIRECT,
                'access_token': 'acc',
                'refresh_token': 'ref',
            },
        }


def test_http_handler_post_with_redirect_url_returns_json() -> None:
    # Arrange
    event_model, patcher = with_registered_controller(
        'register', 'verify-magic-link', _MagicLinkController,
    )
    event = {
        'httpMethod': 'POST',
        'body': json.dumps(
            {
                'operation': 'register',
                'action': 'verify-magic-link',
                'token': 'a' * 32,
            },
        ),
        'headers': {'origin': 'https://the-full-stack.com'},
    }

    # Act
    with patcher:
        response = http_handler(
            event,
            event_model=event_model,
            cors_origin='echo',
            success_status=200,
        )

    # Assert: 200 JSON con los tokens, NO 302.
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['redirect_url'] == _REDIRECT
    assert body['access_token'] == 'acc'
    assert 'Location' not in response['headers']
