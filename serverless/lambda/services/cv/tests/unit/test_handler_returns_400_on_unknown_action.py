"""Handler — action invalida devuelve HTTP 400.

Given un evento GET con un action que no existe (no hay controller),
When lambda_handler lo procesa,
Then devuelve HTTP 400 (validation falla).
"""

from unittest.mock import MagicMock

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


def test_handler_returns_400_on_unknown_action():
    import handler

    # Arrange
    event = {
        'httpMethod': 'GET',
        'path': '/cv',
        'queryStringParameters': {
            'operation': 'cv',
            'action': 'foobar_no_existe',
        },
        'headers': {},
        'requestContext': {'identity': {'sourceIp': '127.0.0.1'}},
    }

    # Act
    response = handler.lambda_handler(event, _context())

    # Assert
    assert response['statusCode'] == 400


def test_handler_returns_400_on_missing_operation():
    """Given GET sin operation/action, Then HTTP 400."""
    import handler

    event = {
        'httpMethod': 'GET',
        'path': '/cv',
        'queryStringParameters': {'niche': 'fintech'},
        'headers': {},
        'requestContext': {'identity': {'sourceIp': '127.0.0.1'}},
    }

    response = handler.lambda_handler(event, _context())
    assert response['statusCode'] == 400
