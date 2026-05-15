"""Tests del handler completo de contact_form (end-to-end con moto)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
import respx

from contact_form.handler import lambda_handler
from contact_form.turnstile import TURNSTILE_SITEVERIFY_URL

pytestmark = pytest.mark.unit


@dataclass
class MockLambdaContext:
    """Mock minimo del Lambda context para Powertools logger."""

    function_name: str = 'test-fn'
    memory_limit_in_mb: int = 512
    invoked_function_arn: str = 'arn:aws:lambda:us-east-1:000000000000:function:test'
    aws_request_id: str = 'test-request-id'

    def get_remaining_time_in_millis(self) -> int:
        return 30000


def _ctx() -> Any:
    return MockLambdaContext()


def _build_event(
    *,
    body: dict | None = None,
    ip: str = '1.2.3.4',
    origin: str = 'https://the-full-stack.com',
    user_agent: str = 'Mozilla/5.0',
) -> dict:
    """Helper: build API GW REST proxy event."""
    headers = {
        'Content-Type': 'application/json',
        'Origin': origin,
        'CF-Connecting-IP': ip,
        'User-Agent': user_agent,
    }
    return {
        'httpMethod': 'POST',
        'path': '/contact',
        'headers': headers,
        'body': json.dumps(body) if body else '',
        'requestContext': {
            'identity': {'sourceIp': ip},
            'requestId': 'test-req-id',
            'stage': 'test',
        },
    }


class TestLambdaHandler:
    """lambda_handler - flujo end-to-end."""

    @respx.mock
    def test_when_valid_form_then_201_with_contact_id(
        self, contact_form_aws: None
    ) -> None:
        """
        Given form valido + Turnstile mock success,
        When invoke handler,
        Then 201 con contact_id en body.
        """
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={'success': True, 'hostname': 'the-full-stack.com'},
            )
        )

        event = _build_event(body={
            'name': 'Pablo Contreras',
            'email': 'user@example.com',
            'message': 'Hola, me interesa colaborar contigo.',
            'cf_token': 'x' * 30,
            'niche': 'fintech',
        })

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert 'contact_id' in body
        assert len(body['contact_id']) == 36
        assert response['headers']['Access-Control-Allow-Origin'] == 'https://the-full-stack.com'

    def test_when_invalid_json_then_400(self, contact_form_aws: None) -> None:
        """
        Given body con JSON malformado,
        When invoke handler,
        Then 400 con code INVALID_JSON.
        """
        event = _build_event()
        event['body'] = '{not valid json'

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['code'] == 'INVALID_JSON'

    def test_when_invalid_input_then_400(self, contact_form_aws: None) -> None:
        """
        Given body sin name (campo requerido),
        When invoke handler,
        Then 400 con code INVALID_INPUT.
        """
        event = _build_event(body={
            'email': 'user@example.com',
            'message': 'Mensaje sin nombre',
            'cf_token': 'x' * 30,
        })

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['code'] == 'INVALID_INPUT'

    @respx.mock
    def test_when_turnstile_invalid_then_403_captcha_invalid(
        self, contact_form_aws: None
    ) -> None:
        """
        Given Turnstile retorna success=false,
        When invoke handler,
        Then 403 con code CAPTCHA_INVALID.
        """
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    'success': False,
                    'error-codes': ['timeout-or-duplicate'],
                },
            )
        )

        event = _build_event(body={
            'name': 'Pablo',
            'email': 'user@example.com',
            'message': 'Mensaje de prueba',
            'cf_token': 'x' * 30,
        })

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 403
        body = json.loads(response['body'])
        assert body['code'] == 'CAPTCHA_INVALID'

    def test_when_bypass_secret_matches_in_dev_then_201(
        self,
        contact_form_aws: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Given STAGE=dev + cf_token vacio + header X-Turnstile-Bypass-Secret
        matchea el SSM bypass param,
        When invoke handler,
        Then 201 (skip Turnstile, no HTTP call a CF).
        """
        monkeypatch.setenv('STAGE', 'dev')
        monkeypatch.setenv(
            'SSM_TURNSTILE_BYPASS_PATH', '/portfolio/dev/turnstile-bypass-secret'
        )
        monkeypatch.setattr(
            'contact_form.turnstile.get_secret',
            lambda _path: 'test-bypass-key',
        )

        event = _build_event(body={
            'name': 'Pablo Test',
            'email': 'user@example.com',
            'message': 'Bypass test message',
            'cf_token': '',
        })
        event['headers']['X-Turnstile-Bypass-Secret'] = 'test-bypass-key'

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 201
