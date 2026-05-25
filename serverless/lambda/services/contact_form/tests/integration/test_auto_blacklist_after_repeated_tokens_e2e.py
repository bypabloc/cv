"""Integration E2E — auto-blacklist tras 3+ tokens validos en la ventana.

Given 3 requests consecutivas desde la misma IP, todas con Turnstile
     valido (heuristica de bot usando un Turnstile solver),
When se invoca el `lambda_handler` end-to-end 3 veces,
Then las 3 devuelven HTTP 201 y queda creada una rule `ip_blacklist`
     para esa IP en la tabla rate-limit-rules (con expires_at).
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.integration._fixtures import (
    _api_gw_event,
    _get_blacklist_rule,
    _lambda_context,
    _valid_body,
)

pytestmark = pytest.mark.integration


@respx.mock
def test_auto_blacklist_after_repeated_tokens_e2e(aws_env):
    import handler

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    ip = '198.51.100.29'

    def _submit() -> dict:
        return handler.lambda_handler(
            _api_gw_event(body=_valid_body(), ip=ip), _lambda_context()
        )

    # Act
    statuses = [_submit()['statusCode'] for _ in range(3)]

    # Assert
    assert statuses == [201, 201, 201]
    rule = _get_blacklist_rule(ip)
    assert rule['kind'] == 'ip_blacklist'
    assert rule['action'] == 'block'
    assert int(rule['expires_at']) > 0
