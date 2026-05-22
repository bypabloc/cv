"""Handler — GET ?action=get end-to-end (con cv_repository mockeado).

Given un evento API Gateway GET /cv?operation=cv&action=get,
When lambda_handler lo procesa,
Then devuelve HTTP 200 con el CV completo devuelto por el service.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def _context():
    ctx = MagicMock()
    ctx.function_name = 'portfolio-cv-test'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:portfolio-cv-test'
    )
    ctx.aws_request_id = 'test-request-id'
    ctx.get_remaining_time_in_millis = lambda: 30000
    return ctx


def test_handler_routes_get_action():
    import handler

    # Arrange
    expected_cv = {
        'profile': {'name': 'Pablo', 'handle': 'bypabloc'},
        'experiences': [],
        'projects': [],
        'certificates': [],
        'awards': [],
        'education': [],
        'languages': [],
        'references': [],
        'skillCategories': [],
    }

    event = {
        'httpMethod': 'GET',
        'path': '/cv',
        'queryStringParameters': {
            'operation': 'cv',
            'action': 'get',
            'niche': 'fintech',
            'locale': 'es',
        },
        'headers': {'origin': 'https://the-full-stack.com'},
        'requestContext': {'identity': {'sourceIp': '127.0.0.1'}},
    }

    with patch(
        'services.cv_service._get_full_cv',
        return_value=expected_cv,
    ):
        # Act
        response = handler.lambda_handler(event, _context())

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['profile']['name'] == 'Pablo'
