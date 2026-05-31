"""Controller contact/create — normalizacion del caso de exito.

Given un payload valido + entorno AWS mockeado (rate-limit, Turnstile y
     persistencia operativos),
When el controller Create ejecuta su ciclo run(),
Then devuelve {is_valid: True, code: 0} con el contact_id en data (el
     contacto se persiste inline a Neon e invoca send_email async).
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

pytestmark = pytest.mark.unit


@respx.mock
def test_create_controller_normalizes_success(
    mock_neon_writes: list[dict],
    mock_invoke: list[dict],
    contact_form_aws: None,
) -> None:
    from controllers.contact.create import Create

    # Arrange: Turnstile success + persistencia/invoke mockeados.
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
            'bypass_token': None,
        },
    }

    # Act
    result = Create(event=event_data).run()

    # Assert
    assert result['is_valid'] is True
    assert result['code'] == 0
    assert len(result['data']['contact_id']) == 36
    # El contacto se persistio y se invoco send_email async.
    assert len(mock_neon_writes) == 1
    assert len(mock_invoke) == 1
