"""El handler responde 401 a una action sin header Authorization.

Given una request content.catalogs SIN Authorization,
When se invoca lambda_handler (require_active_user REAL),
Then 401 — el auth corta ANTES de admin/rate-limit/DB.
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


def test_handler_401_missing_authorization():
    from handler import lambda_handler

    event = {
        'httpMethod': 'POST',
        'path': '/cv-admin',
        'headers': {
            'Content-Type': 'application/json',
            'Origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'CF-Connecting-IP': '203.0.113.10',
        },
        'queryStringParameters': None,
        'body': '{"operation":"content","action":"catalogs","data":{}}',
        'requestContext': {
            'identity': {'sourceIp': '203.0.113.10'},
            'requestId': 'r3',
            'stage': 'dev',
        },
    }

    response = lambda_handler(event, _fake_context())

    assert response['statusCode'] == 401
