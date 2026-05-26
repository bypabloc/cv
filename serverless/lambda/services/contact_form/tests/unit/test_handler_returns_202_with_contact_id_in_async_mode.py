"""Handler — exito en modo async devuelve HTTP 202 con contact_id.

Given ASYNC_MODE=true + un evento API Gateway con form valido y
     Turnstile mock success,
When lambda_handler procesa el evento,
Then devuelve HTTP 202 con `{contact_id, created_at, accepted: true}`
     en el body, el echo CORS y publica EXACTAMENTE 1 mensaje a SQS.

Spec lambdas-async-sqs (fase 07): el encoder pre-genera el contact_id
(UUIDv7) y lo retorna sin haber tocado Neon ni SES. AC-1.
"""

import json

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_handler_returns_202_with_contact_id_in_async_mode(
    monkeypatch: pytest.MonkeyPatch,
    mock_sqs: list[dict],
    contact_form_aws: None,
) -> None:
    import handler
    from settings.config import AppConfig

    # Arrange: ASYNC mode (default, pero explicito para claridad).
    monkeypatch.setattr(AppConfig, 'async_mode', True)

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
            'niche': 'fintech',
        },
        ip='203.0.113.30',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 202
    body = json.loads(response['body'])
    assert len(body['contact_id']) == 36
    assert body['accepted'] is True
    assert 'created_at' in body
    assert (
        response['headers']['Access-Control-Allow-Origin']
        == 'https://the-full-stack.com'
    )
    assert len(mock_sqs) == 1
    sent = mock_sqs[0]
    assert sent['queue'] == 'contact-form'
    assert sent['payload']['contact_id'] == body['contact_id']
    assert sent['payload']['schema_version'] == 1
    assert sent['payload']['name'] == 'Pablo Contreras'
    assert sent['payload']['email'] == 'user@example.com'
    assert sent['payload']['niche'] == 'fintech'
