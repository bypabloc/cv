"""Controller contact/create — rate-limit agotado.

Given que el rate-limit per-IP esta agotado (check_or_raise levanta
     RateLimitExceededError),
When el controller Create ejecuta su ciclo run(),
Then propaga la excepcion ANTES de validar Turnstile o persistir (el
     handler la traduce al HTTP 429).
"""

import pytest
from shared.rate_limit import RateLimitExceededError

pytestmark = pytest.mark.unit


def test_create_controller_raises_on_rate_limit(
    contact_form_aws, monkeypatch
):
    import controllers.contact.create as create_mod
    from controllers.contact.create import Create

    # Arrange: el rate-limit rechaza la IP.
    def _reject(**_kwargs):
        msg = 'rate limit agotado'
        raise RateLimitExceededError(msg, code='RATE_LIMIT_EXCEEDED')

    monkeypatch.setattr(create_mod, 'check_or_raise', _reject)
    event_data = {
        'name': 'Pablo Contreras',
        'email': 'user@example.com',
        'message': 'Hola, me interesa colaborar contigo.',
        'cf_token': 'x' * 30,
        '_meta': {'ip': '203.0.113.22', 'country': 'CL'},
    }

    # Act / Assert
    with pytest.raises(RateLimitExceededError) as exc_info:
        Create(event=event_data).run()
    assert exc_info.value.code == 'RATE_LIMIT_EXCEEDED'
