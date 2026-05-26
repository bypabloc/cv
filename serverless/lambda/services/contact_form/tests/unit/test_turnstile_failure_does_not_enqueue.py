"""Handler — Turnstile invalido NO encola el mensaje a SQS.

Given ASYNC_MODE=true + Turnstile responde success=false,
When lambda_handler procesa el evento POST /contact,
Then devuelve HTTP 403 (CAPTCHA_INVALID) Y `send_to_queue` NUNCA se
     invoca (la verificacion gating debe correr ANTES del branch async).

Spec lambdas-async-sqs (fase 07): la defensa anti-bot va siempre
antes del encolar — un token invalido NO debe consumir capacidad de la
cola. AC-2.
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_turnstile_failure_does_not_enqueue(
    monkeypatch: pytest.MonkeyPatch,
    mock_sqs: list[dict],
    contact_form_aws: None,
) -> None:
    import handler
    from settings.config import AppConfig

    # Arrange: async mode + Turnstile rechaza
    monkeypatch.setattr(AppConfig, 'async_mode', True)
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
    # NUNCA se publica si Turnstile falla.
    assert mock_sqs == []
