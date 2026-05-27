"""Handler — modo async NO toca SES (`send_owner_email` no se invoca).

Given ASYNC_MODE=true + un evento API Gateway con form valido y
     Turnstile mock success,
When lambda_handler procesa el evento (encoder publica a SQS),
Then `send_owner_email` NUNCA se invoca (el worker lo hara al consumir
     el mensaje), y NO se llama tampoco a `process_contact_form` (que es
     el path sync legacy).

Spec lambdas-async-sqs (fase 07): el encoder no debe tocar Neon ni SES
en modo async. Si lo hace, falla el aislamiento de responsabilidades
entre encoder y worker.
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_async_mode_does_not_call_send_email(
    monkeypatch: pytest.MonkeyPatch,
    mock_sqs: list[dict],
    contact_form_aws: None,
) -> None:
    import handler
    from services import contact_service
    from settings.config import AppConfig

    # Arrange
    monkeypatch.setattr(AppConfig, 'async_mode', True)

    # Spy sobre send_owner_email y process_contact_form: si alguno se
    # llama en modo async, el test falla.
    email_calls: list[dict] = []
    sync_calls: list[dict] = []

    def _spy_email(contact: dict) -> str:
        email_calls.append(contact)
        return 'fake-msg-id'

    def _spy_sync(**kwargs) -> dict:
        sync_calls.append(kwargs)
        return {'contact_id': 'x' * 36, 'created_at': '2026-05-25T00:00:00Z'}

    monkeypatch.setattr(contact_service, 'send_owner_email', _spy_email)
    monkeypatch.setattr(
        'controllers.contact.create.process_contact_form',
        _spy_sync,
    )

    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    event = api_gw_event(
        body={
            'name': 'Pablo Contreras',
            'email': 'user@example.com',
            'message': 'Hola, me interesa colaborar contigo.',
            'cf_token': 'x' * 30,
        },
        ip='203.0.113.31',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 202
    assert email_calls == []
    assert sync_calls == []
    assert len(mock_sqs) == 1
