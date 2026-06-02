"""shared.lambda_kit.http_dispatch — GET con redirect_url -> 302.

Given un controller que devuelve is_valid=True con `redirect_url` en data
(el caso del magic-link verify),
When http_handler procesa un request GET (query params),
Then responde 302 con header Location = redirect_url y body vacio.

Cubre el callback del magic-link: el browser navega al link del email
(GET top-level), el Lambda redirige al admin/callback con los tokens en
el fragment hash.
"""

from __future__ import annotations

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
    '#access=acc&refresh=ref&user_id=u1&email=x@y.com'
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


def test_http_handler_get_with_redirect_url_returns_302() -> None:
    # Arrange
    event_model, patcher = with_registered_controller(
        'register', 'verify-magic-link', _MagicLinkController,
    )
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {
            'operation': 'register',
            'action': 'verify-magic-link',
            'token': 'a' * 32,
        },
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

    # Assert: 302 con Location = redirect_url, body vacio (sin JSON).
    assert response['statusCode'] == 302
    assert response['headers']['Location'] == _REDIRECT
    assert response['body'] == ''
