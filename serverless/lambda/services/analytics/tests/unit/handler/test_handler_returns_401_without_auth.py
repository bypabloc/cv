"""Handler — request sin Authorization devuelve 401 antes de tocar Neon (AC-23).

Given un evento GET valido a analytics/overview SIN header Authorization,
When lambda_handler lo procesa (auth real, pero el verify del JWT mockeado
  para no tocar SSM/Neon),
Then devuelve HTTP 401 (auth_guard -> jwt_service rechaza la ausencia del
  Bearer ANTES de la query).
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


def test_handler_returns_401_without_auth():
    import handler

    event = {
        'httpMethod': 'GET',
        'path': '/analytics',
        'queryStringParameters': {
            'operation': 'analytics',
            'action': 'overview',
            'from': '2026-04-27',
            'to': '2026-05-27',
        },
        # SIN header authorization.
        'headers': {},
        'requestContext': {'identity': {'sourceIp': '127.0.0.1'}},
    }

    # El auth_guard -> jwt_service.authenticate rechaza la ausencia del
    # Bearer (ApplicationError 401) ANTES de cualquier query a Neon.
    response = handler.lambda_handler(event, _context())
    assert response['statusCode'] == 401
