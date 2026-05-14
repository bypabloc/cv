"""Tests del handler turnstile_validator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
import respx

from turnstile_validator.handler import lambda_handler
from turnstile_validator.service import TURNSTILE_SITEVERIFY_URL

pytestmark = pytest.mark.unit


@dataclass
class MockLambdaContext:
    function_name: str = 'test-validator'
    memory_limit_in_mb: int = 256
    invoked_function_arn: str = 'arn:aws:lambda:us-east-1:000000000000:function:t'
    aws_request_id: str = 'req-id'

    def get_remaining_time_in_millis(self) -> int:
        return 10000


def _ctx() -> Any:
    return MockLambdaContext()


def _build_event(*, body: dict | None = None, ip: str = '1.2.3.4') -> dict:
    return {
        'httpMethod': 'POST',
        'path': '/validate-turnstile',
        'headers': {
            'Content-Type': 'application/json',
            'Origin': 'https://the-full-stack.com',
            'CF-Connecting-IP': ip,
        },
        'body': json.dumps(body) if body else '',
        'requestContext': {
            'identity': {'sourceIp': ip},
            'requestId': 'req-id',
            'stage': 'test',
        },
    }


class TestValidatorHandler:
    @respx.mock
    def test_when_valid_token_then_200_with_valid_true(
        self, turnstile_aws: None
    ) -> None:
        """
        Given Turnstile siteverify success,
        When invoke /validate-turnstile,
        Then 200 con {valid: true, hostname}.
        """
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={'success': True, 'hostname': 'the-full-stack.com'},
            )
        )

        event = _build_event(body={'cf_token': 'x' * 30})
        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['valid'] is True
        assert body['hostname'] == 'the-full-stack.com'

    def test_when_missing_token_then_400(
        self, turnstile_aws: None
    ) -> None:
        """Given sin cf_token, When invoke, Then 400 INVALID_INPUT."""
        event = _build_event(body={})

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 400
        assert json.loads(response['body'])['code'] == 'INVALID_INPUT'

    def test_when_bypass_secret_then_200(
        self,
        turnstile_aws: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given bypass_secret matchea, When invoke, Then 200 sin CF call."""
        monkeypatch.setenv('TURNSTILE_BYPASS_SECRET', 'bypass-123')

        event = _build_event(body={'cf_token': 'x' * 30})
        event['headers']['X-Turnstile-Bypass-Secret'] = 'bypass-123'

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['valid'] is True
