"""Controller contact/create — Turnstile rechaza el token.

Given un payload valido pero Turnstile responde success=false,
When el controller Create ejecuta su ciclo run(),
Then propaga TurnstileError con code CAPTCHA_INVALID (el handler lo
     traduce al HTTP 403).
"""

import httpx
import pytest
import respx

from shared.core.exceptions import TurnstileError
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

pytestmark = pytest.mark.unit


@respx.mock
def test_create_controller_raises_on_invalid_turnstile(contact_form_aws):
    from controllers.contact.create import Create

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200,
            json={'success': False, 'error-codes': ['timeout-or-duplicate']},
        )
    )
    event_data = {
        'name': 'Pablo Contreras',
        'email': 'user@example.com',
        'message': 'Hola, me interesa colaborar contigo.',
        'cf_token': 'x' * 30,
        '_meta': {'ip': '203.0.113.21', 'country': 'CL'},
    }

    # Act / Assert
    with pytest.raises(TurnstileError) as exc_info:
        Create(event=event_data).run()
    assert exc_info.value.code == 'CAPTCHA_INVALID'
