"""shared.lambda_kit.http_dispatch.http_handler — inyeccion de _meta.

Given un evento con headers de transporte (user-agent, IP via
     requestContext, country via header CloudFront),
When se invoca http_handler,
Then el controller recibe data['_meta'] con ip, country, user_agent y
     bypass_secret extraidos del evento.
"""

from __future__ import annotations

from typing import Any, ClassVar

import pytest
from pydantic import BaseModel
from shared.lambda_kit import BaseController, http_handler
from tests.unit.shared.lambda_kit._http_handler_helpers import (
    with_registered_controller,
)

pytestmark = pytest.mark.unit


class _MetaCapturingModel(BaseModel):
    model_config = {'extra': 'allow'}


class _MetaCapturingController(BaseController):
    event_model = _MetaCapturingModel
    captured: ClassVar[dict[str, Any]] = {}

    def execute(self) -> dict:
        _MetaCapturingController.captured = dict(self.event or {})
        return {'is_valid': True, 'data': {'ok': True}, 'code': 0}


def test_http_handler_injects_meta_from_headers() -> None:
    # Arrange
    _MetaCapturingController.captured = {}
    event_model, patcher = with_registered_controller(
        'cv', 'get', _MetaCapturingController
    )

    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {'operation': 'cv', 'action': 'get'},
        'headers': {
            'user-agent': 'curl/8.0',
            'cf-ipcountry': 'CL',
            'x-turnstile-bypass-secret': 'secret-123',
            'origin': 'https://the-full-stack.com',
        },
        'requestContext': {
            'identity': {'sourceIp': '203.0.113.42'},
        },
    }

    # Act
    with patcher:
        http_handler(
            event,
            event_model=event_model,
            cors_origin='public',
        )

    # Assert
    captured_meta = _MetaCapturingController.captured.get('_meta')
    assert captured_meta == {
        'ip': '203.0.113.42',
        'country': 'CL',
        'user_agent': 'curl/8.0',
        'bypass_secret': 'secret-123',
        # cloudfront_meta vacio porque el evento de test no trae headers
        # cloudfront-* (REGIONAL). En Edge-Optimized llegan ~22 headers.
        'cloudfront_meta': {},
    }
