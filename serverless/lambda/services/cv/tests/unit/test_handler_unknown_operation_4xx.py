"""El handler rechaza una operation desconocida con 4xx.

Given una request con operation=unknown,
When se invoca lambda_handler,
Then http_handler devuelve un response de error (4xx), NO 200.
"""

def _fake_context():
    """LambdaContext stub para los decoradores Powertools."""
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.aws_request_id = 'test-request-id'
    ctx.function_name = 'cv-admin-test'
    ctx.function_version = '$LATEST'
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:123456789012:function:cv-admin-test'
    )
    ctx.memory_limit_in_mb = 256
    ctx.get_remaining_time_in_millis = lambda: 15000
    return ctx


def test_handler_unknown_operation_4xx():
    from handler import lambda_handler

    event = {
        'httpMethod': 'POST',
        'path': '/cv',
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

    assert response['statusCode'] == 400
