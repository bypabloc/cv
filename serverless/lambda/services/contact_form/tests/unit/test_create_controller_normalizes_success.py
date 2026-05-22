"""Controller contact/create — normalizacion del caso de exito.

Given un payload valido y el entorno AWS mockeado (rate-limit, Turnstile
     y persistencia operativos),
When el controller Create ejecuta su ciclo run(),
Then devuelve {is_valid: True, code: 0} con el contact_id en data.
"""

import httpx
import pytest
import respx

from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

pytestmark = pytest.mark.unit


@respx.mock
def test_create_controller_normalizes_success(contact_form_aws):
    from controllers.contact.create import Create

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    event_data = {
        'name': 'Pablo Contreras',
        'email': 'user@example.com',
        'message': 'Hola, me interesa colaborar contigo.',
        'cf_token': 'x' * 30,
        '_meta': {
            'ip': '203.0.113.20',
            'country': 'CL',
            'user_agent': 'Mozilla/5.0',
            'bypass_secret': None,
        },
    }

    # Act
    result = Create(event=event_data).run()

    # Assert
    assert result['is_valid'] is True
    assert result['code'] == 0
    assert len(result['data']['contact_id']) == 36
