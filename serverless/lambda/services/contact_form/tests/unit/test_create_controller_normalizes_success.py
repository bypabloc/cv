"""Controller contact/create — normalizacion del caso de exito sync.

Given ASYNC_MODE=false (sync legacy) + payload valido + entorno AWS
     mockeado (rate-limit, Turnstile y persistencia operativos),
When el controller Create ejecuta su ciclo run(),
Then devuelve {is_valid: True, code: 0} con el contact_id en data.

Spec lambdas-async-sqs (fase 07): este test cubre el path sync legacy.
La normalizacion del path async (encoder -> SQS -> 202) se cubre en
test_handler_returns_202_with_contact_id_in_async_mode.py y los demas
test_async_*.
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

pytestmark = pytest.mark.unit


@respx.mock
def test_create_controller_normalizes_success(
    monkeypatch: pytest.MonkeyPatch,
    mock_neon_writes: list[dict],
    contact_form_aws: None,
) -> None:
    from controllers.contact.create import Create
    from settings.config import AppConfig

    # Arrange: forzar SYNC mode (sync legacy persiste + envia email).
    monkeypatch.setattr(AppConfig, 'async_mode', False)

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
