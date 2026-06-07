"""Handler — routing GET + validacion de operation/action (AC-4).

Given eventos GET con operation/action invalidos,
When lambda_handler los procesa,
Then devuelve HTTP 400 (la resolucion del controller falla).
"""

from unittest.mock import MagicMock


def _context():
    ctx = MagicMock()
    ctx.function_name = 'portfolio-analytics-test'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = 'arn:aws:lambda:us-east-1:000000000000:function:portfolio-analytics-test'
    ctx.aws_request_id = 'test-request-id'
    ctx.get_remaining_time_in_millis = lambda: 30000
    return ctx


def test_handler_returns_400_on_unknown_operation():
    import handler

    event = {
        'httpMethod': 'GET',
        'path': '/analytics',
        'queryStringParameters': {'operation': 'foo', 'action': 'bar'},
        'headers': {},
        'requestContext': {'identity': {'sourceIp': '127.0.0.1'}},
    }

    response = handler.lambda_handler(event, _context())
    assert response['statusCode'] == 400


def test_handler_returns_400_on_unknown_action():
    import handler

    event = {
        'httpMethod': 'GET',
        'path': '/analytics',
        'queryStringParameters': {
            'operation': 'analytics',
            'action': 'no_existe',
        },
        'headers': {},
        'requestContext': {'identity': {'sourceIp': '127.0.0.1'}},
    }

    response = handler.lambda_handler(event, _context())
    assert response['statusCode'] == 400
