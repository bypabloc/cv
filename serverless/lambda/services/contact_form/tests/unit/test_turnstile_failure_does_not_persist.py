"""Handler — Turnstile invalido NO persiste ni invoca send_email.

Given Turnstile responde success=false,
When lambda_handler procesa el evento POST /contact,
Then devuelve HTTP 403 (CAPTCHA_INVALID) Y `invoke_async` NUNCA se invoca
     (la verificacion gating debe correr ANTES de persistir / notificar).

La defensa anti-bot va siempre antes de escribir a Neon — un token
invalido NO debe persistir un contacto ni gatillar un email. AC-2.
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_turnstile_failure_does_not_persist(
    mock_neon_writes: list[dict],
    mock_invoke: list[dict],
    contact_form_aws: None,
) -> None:
    import handler

    # Arrange: Turnstile rechaza.
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200,
            json={'success': False, 'error-codes': ['timeout-or-duplicate']},
        )
    )
    event = api_gw_event(
        body={
            'name': 'Pablo Contreras',
            'email': 'user@example.com',
            'message': 'Hola, me interesa colaborar contigo.',
            'cf_token': 'x' * 30,
        },
        ip='203.0.113.50',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 403
    # NUNCA se persiste ni se invoca send_email si Turnstile falla.
    assert mock_neon_writes == []
    assert mock_invoke == []
