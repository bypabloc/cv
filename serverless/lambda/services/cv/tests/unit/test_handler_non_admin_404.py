"""El handler responde 404 (anti-enumeration) a un user NO-admin.

Given un user autenticado cuyo email NO esta en la whitelist SSM
(require_admin REAL contra ADMIN_EMAILS del conftest),
When se invoca lambda_handler con content.catalogs,
Then 404 NOT_FOUND — oculta la existencia del endpoint.
"""

from unittest.mock import MagicMock


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


def test_handler_non_admin_404(monkeypatch):
    from handler import lambda_handler
    from services import permission_checker

    non_admin = MagicMock(id='u1', email='visitor@example.com')
    monkeypatch.setattr(
        permission_checker,
        'require_active_user',
        lambda *_a, **_k: non_admin,
    )

    event = {
        'httpMethod': 'POST',
        'path': '/cv',
        'headers': {
            'Content-Type': 'application/json',
            'Origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'CF-Connecting-IP': '203.0.113.10',
            'Authorization': 'Bearer FAKE-JWT',
        },
        'queryStringParameters': None,
        'body': '{"operation":"content","action":"catalogs","data":{}}',
        'requestContext': {
            'identity': {'sourceIp': '203.0.113.10'},
            'requestId': 'r4',
            'stage': 'dev',
        },
    }

    response = lambda_handler(event, _fake_context())

    assert response['statusCode'] == 404
