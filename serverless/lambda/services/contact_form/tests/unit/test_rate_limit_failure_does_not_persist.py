"""Handler — rate-limit excedido NO persiste ni invoca send_email.

Given una IP rate-limited (check_or_raise lanza RateLimitExceededError),
When lambda_handler procesa el evento,
Then devuelve HTTP 429 Y `invoke_async` NUNCA se invoca (el rate-limit
     debe correr ANTES de persistir / notificar).

El rate-limit es la primera defensa y corre antes de Turnstile y antes
de escribir a Neon. AC-3.
"""

import pytest
from shared.rate_limit.exceptions import RateLimitExceededError

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


def test_rate_limit_failure_does_not_persist(
    monkeypatch: pytest.MonkeyPatch,
    mock_neon_writes: list[dict],
    mock_invoke: list[dict],
    contact_form_aws: None,
) -> None:
    import controllers.contact.create as create_mod
    import handler

    # Arrange: el rate-limit rechaza la IP.
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
    # NUNCA se persiste ni se invoca send_email si el rate-limit corta.
    assert mock_neon_writes == []
    assert mock_invoke == []
