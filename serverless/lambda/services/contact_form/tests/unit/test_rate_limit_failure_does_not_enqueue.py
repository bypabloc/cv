"""Handler — rate-limit excedido NO encola el mensaje a SQS.

Given ASYNC_MODE=true + IP rate-limited (check_or_raise lanza
     RateLimitExceededError),
When lambda_handler procesa el evento,
Then devuelve HTTP 429 Y `send_to_queue` NUNCA se invoca (rate-limit
     debe correr ANTES del branch async para no gastar capacidad SQS).

Spec lambdas-async-sqs (fase 07): el rate-limit es la primera defensa
y corre antes de Turnstile y antes del encolar. AC-3.
"""

import pytest
from shared.rate_limit.exceptions import RateLimitExceededError

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


def test_rate_limit_failure_does_not_enqueue(
    monkeypatch: pytest.MonkeyPatch,
    mock_sqs: list[dict],
    contact_form_aws: None,
) -> None:
    import controllers.contact.create as create_mod
    import handler
    from settings.config import AppConfig

    # Arrange: ASYNC mode + el rate-limit rechaza la IP.
    monkeypatch.setattr(AppConfig, 'async_mode', True)

    def _reject(**_kwargs):
        msg = 'rate limit agotado'
        raise RateLimitExceededError(msg, code='RATE_LIMIT_EXCEEDED')

    monkeypatch.setattr(create_mod, 'check_or_raise', _reject)

    event = api_gw_event(
        body={
            'name': 'Pablo Contreras',
            'email': 'user@example.com',
            'message': 'Hola, me interesa colaborar contigo.',
            'cf_token': 'x' * 30,
        },
        ip='203.0.113.51',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 429
    # NUNCA se publica si el rate-limit corta.
    assert mock_sqs == []
