"""El handler delega en `http_handler` con los parametros del Lambda auth.

Una request invalida (operation=unknown) hace que `http_handler`
devuelva un response de error (404/400). NO probamos un flujo feliz
porque los controllers concretos llegan en PR 7/8.

El handler decorado con powertools requiere un `LambdaContext`
fake; usamos un MagicMock con los atributos minimos.
"""

from unittest.mock import MagicMock


def _fake_context():
    """LambdaContext stub para los decoradores Powertools."""
    ctx = MagicMock()
    ctx.aws_request_id = 'test-request-id'
    ctx.function_name = 'auth-test'
    ctx.function_version = '$LATEST'
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:123456789012:function:auth-test'
    )
    ctx.memory_limit_in_mb = 384
    ctx.get_remaining_time_in_millis = lambda: 15000
    return ctx


def test_handler_returns_error_for_unknown_operation():
    """operation=unknown -> 4xx (no se llama a ningun controller real)."""
    from handler import lambda_handler

    event = {
        'httpMethod': 'POST',
        'path': '/auth',
        'headers': {
            'Content-Type': 'application/json',
            'Origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'CF-Connecting-IP': '203.0.113.10',
        },
        'queryStringParameters': None,
        'body': ('{"operation":"unknown","action":"start","data":{}}'),
        'requestContext': {
            'identity': {'sourceIp': '203.0.113.10'},
            'requestId': 'r1',
            'stage': 'dev',
        },
    }

    response = lambda_handler(event, _fake_context())

    assert 'statusCode' in response
    # http_handler traduce un controller_not_found a 400/404 — sea cual
    # sea, NO es 200.
    assert response['statusCode'] != 200


def test_handler_returns_error_for_missing_action():
    """operation valida pero sin action -> 4xx (validate_event falla)."""
    from handler import lambda_handler

    event = {
        'httpMethod': 'POST',
        'path': '/auth',
        'headers': {
            'Content-Type': 'application/json',
            'Origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'CF-Connecting-IP': '203.0.113.10',
        },
        'queryStringParameters': None,
        'body': ('{"operation":"register","data":{}}'),
        'requestContext': {
            'identity': {'sourceIp': '203.0.113.10'},
            'requestId': 'r2',
            'stage': 'dev',
        },
    }

    response = lambda_handler(event, _fake_context())

    assert response['statusCode'] != 200
