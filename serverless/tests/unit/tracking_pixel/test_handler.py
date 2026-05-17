"""Tests del handler tracking_pixel (end-to-end con moto)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from tracking_pixel.handler import lambda_handler

pytestmark = pytest.mark.unit


@dataclass
class MockLambdaContext:
    function_name: str = 'test-track'
    memory_limit_in_mb: int = 256
    invoked_function_arn: str = (
        'arn:aws:lambda:us-east-1:000000000000:function:track'
    )
    aws_request_id: str = 'test-req-id'

    def get_remaining_time_in_millis(self) -> int:
        return 10000


def _ctx() -> Any:
    return MockLambdaContext()


def _build_event(*, body: dict | None = None, ip: str = '1.2.3.4') -> dict:
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://the-full-stack.com',
        'CF-Connecting-IP': ip,
        'User-Agent': 'Mozilla/5.0 Chrome/118',
    }
    return {
        'httpMethod': 'POST',
        'path': '/track',
        'headers': headers,
        'body': json.dumps(body) if body else '',
        'requestContext': {
            'identity': {'sourceIp': ip},
            'requestId': 'req-id',
            'stage': 'test',
        },
    }


class TestTrackingHandler:
    """lambda_handler - tracking_pixel."""

    def test_when_valid_event_then_204_no_content(
        self, tracking_aws: None
    ) -> None:
        """
        Given event valido,
        When invoke handler,
        Then 204 sin body.
        """
        event = _build_event(
            body={
                'session_id': 'session-uuid-1234567890abcdef',
                'event_id': 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
                'event_type_id': '019e372b-e0a7-7154-8279-8829bcf6a08c',
                'page_url': 'https://the-full-stack.com/projects',
                'page_title': 'Projects',
                'page_path': '/projects',
                'utm_source': 'twitter',
                'viewport_width': 1920,
                'viewport_height': 1080,
                'niche': 'fintech',
            }
        )

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 204
        assert response['body'] == ''

    def test_when_missing_session_id_then_400(self, tracking_aws: None) -> None:
        """Given sin session_id, When invoke, Then 400 INVALID_INPUT."""
        event = _build_event(
            body={
                'page_url': 'https://the-full-stack.com/',
            }
        )

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 400

    def test_when_invalid_json_then_400(self, tracking_aws: None) -> None:
        """Given body malformado, When invoke, Then 400 INVALID_JSON."""
        event = _build_event()
        event['body'] = '{not valid'

        response = lambda_handler(event, _ctx())

        assert response['statusCode'] == 400
        assert json.loads(response['body'])['code'] == 'INVALID_JSON'
