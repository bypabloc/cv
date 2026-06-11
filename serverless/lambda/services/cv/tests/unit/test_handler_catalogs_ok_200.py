"""El handler responde 200 con el resultado del service en el happy path.

Given un admin autenticado (guards mockeados) y catalogs mockeado,
When se invoca lambda_handler con content.catalogs,
Then 200 con el body JSON del service.
"""

import json
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


def test_handler_catalogs_ok_200(monkeypatch):
    from controllers import _base
    from handler import lambda_handler
    from services import catalog_service, permission_checker

    admin = MagicMock(id='u1', email='admin@example.com')
    monkeypatch.setattr(
        permission_checker,
        'require_active_user',
        lambda *_a, **_k: admin,
    )
    monkeypatch.setattr(_base, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        catalog_service,
        'catalogs',
        MagicMock(
            return_value={
                'niches': ['generic'], 'skills': [], 'techTags': [],
            },
        ),
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
            'requestId': 'r5',
            'stage': 'dev',
        },
    }

    response = lambda_handler(event, _fake_context())

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body == {'niches': ['generic'], 'skills': [], 'techTags': []}
