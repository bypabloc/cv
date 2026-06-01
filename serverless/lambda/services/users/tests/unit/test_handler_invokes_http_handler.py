"""El handler de `users` delega en http_handler con los params del Lambda.

Given una request con operation invalida o sin Authorization,
When se invoca lambda_handler,
Then http_handler devuelve un response de error (4xx), NO 200.

El handler decorado con powertools requiere un LambdaContext fake.
"""

from unittest.mock import MagicMock


def _fake_context():
    """LambdaContext stub para los decoradores Powertools."""
    ctx = MagicMock()
    ctx.aws_request_id = 'test-request-id'
    ctx.function_name = 'users-test'
    ctx.function_version = '$LATEST'
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:123456789012:function:users-test'
    )
    ctx.memory_limit_in_mb = 384
    ctx.get_remaining_time_in_millis = lambda: 15000
    return ctx


def test_handler_returns_error_for_unknown_operation():
    """operation=unknown -> 4xx (no se llama a ningun controller real)."""
    from handler import lambda_handler

    event = {
        'httpMethod': 'POST',
        'path': '/users',
        'headers': {
            'Content-Type': 'application/json',
            'Origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'CF-Connecting-IP': '203.0.113.10',
        },
        'queryStringParameters': None,
        'body': '{"operation":"unknown","action":"get","data":{}}',
        'requestContext': {
            'identity': {'sourceIp': '203.0.113.10'},
            'requestId': 'r1',
            'stage': 'dev',
        },
    }

    response = lambda_handler(event, _fake_context())

    assert 'statusCode' in response
    assert response['statusCode'] != 200


def test_handler_returns_error_for_missing_action():
    """operation valida pero sin action -> 4xx (validate_event falla)."""
    from handler import lambda_handler

    event = {
        'httpMethod': 'POST',
        'path': '/users',
        'headers': {
            'Content-Type': 'application/json',
            'Origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'CF-Connecting-IP': '203.0.113.10',
        },
        'queryStringParameters': None,
        'body': '{"operation":"profile","data":{}}',
        'requestContext': {
            'identity': {'sourceIp': '203.0.113.10'},
            'requestId': 'r2',
            'stage': 'dev',
        },
    }

    response = lambda_handler(event, _fake_context())

    assert response['statusCode'] != 200
