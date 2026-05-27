"""Handler — sync legacy mode (flag false) sigue devolviendo HTTP 201.

Given ASYNC_MODE=false (rollback path) + un evento API Gateway con form
     valido y Turnstile mock success,
When lambda_handler procesa el evento,
Then devuelve HTTP 201 con el contact_id y NO publica nada a SQS
     (process_contact_form persiste sincronamente).

Spec lambdas-async-sqs (fase 07): garantiza que flipear la env var a
'false' restaura el flujo viejo sin redeploy del worker. AC-5.
"""

import json

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_handler_returns_201_in_sync_mode_legacy(
    monkeypatch: pytest.MonkeyPatch,
    mock_neon_writes: list[dict],
    mock_sqs: list[dict],
    contact_form_aws: None,
) -> None:
    import handler
    from settings.config import AppConfig

    # Arrange: forzar SYNC mode (rollback path explicito).
    monkeypatch.setattr(AppConfig, 'async_mode', False)

    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    event = api_gw_event(
        body={
            'name': 'Pablo Contreras',
            'email': 'user@example.com',
            'message': 'Hola, me interesa colaborar contigo en fintech.',
            'cf_token': 'x' * 30,
            'niche': 'fintech',
        },
        ip='203.0.113.40',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert len(body['contact_id']) == 36
    # SYNC mode NUNCA toca SQS.
    assert mock_sqs == []
    # SYNC mode SI persiste a Neon (mock_neon_writes captura el insert).
    assert len(mock_neon_writes) == 1
    assert mock_neon_writes[0]['email'] == 'user@example.com'
