"""Handler — falla del publish a SQS retorna 5xx (sin fallback a sync).

Given ASYNC_MODE=true + `send_to_queue` levanta `QueuePublishError`
     (SQS caida o IAM mal configurado),
When lambda_handler procesa el evento con form valido y Turnstile OK,
Then devuelve HTTP 5xx (NO 201, NO 202) y NO se ejecuta el sync
     fallback — el comportamiento es falla explicita.

Spec lambdas-async-sqs (fase 07): un fallback automatico de async a
sync ante fallo SQS seria comportamiento impredecible y dificil de
debuggear. Mejor 5xx explicito + retry del cliente.
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL
from shared.queue import QueuePublishError

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_enqueue_failure_returns_5xx(
    monkeypatch: pytest.MonkeyPatch,
    contact_form_aws: None,
) -> None:
    import handler
    from services import contact_service
    from settings.config import AppConfig

    # Arrange: ASYNC mode + SQS publish falla
    monkeypatch.setattr(AppConfig, 'async_mode', True)

    def _raise(**_kwargs) -> str:
        raise QueuePublishError(
            'contact-form',
            RuntimeError('SQS unavailable'),
        )

    monkeypatch.setattr(contact_service, 'send_to_queue', _raise)

    # Spy sobre process_contact_form: NO debe llamarse (no hay fallback).
    sync_calls: list[dict] = []

    def _spy_sync(**kwargs) -> dict:
        sync_calls.append(kwargs)
        return {'contact_id': 'x' * 36, 'created_at': '2026-05-25T00:00:00Z'}

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
        ip='203.0.113.52',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 500
    # NO se hace fallback a sync — comportamiento explicito.
    assert sync_calls == []
