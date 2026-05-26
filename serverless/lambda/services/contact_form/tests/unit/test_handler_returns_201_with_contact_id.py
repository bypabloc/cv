"""Handler — exito en modo sync legacy devuelve HTTP 201.

Given ASYNC_MODE=false (rollback path) + un evento API Gateway con un
     form valido y Turnstile mock success,
When lambda_handler procesa el evento,
Then devuelve HTTP 201 con el contact_id en el body y el echo CORS.

Spec lambdas-async-sqs (fase 07): mantiene la garantia del flujo viejo
para el rollback path. El happy-path async (HTTP 202) se cubre en
test_handler_returns_202_with_contact_id_in_async_mode.py.
"""

import json

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.unit._helpers import api_gw_event, lambda_context

pytestmark = pytest.mark.unit


@respx.mock
def test_handler_returns_201_with_contact_id(
    monkeypatch: pytest.MonkeyPatch,
    mock_neon_writes: list[dict],
    contact_form_aws: None,
) -> None:
    import handler
    from settings.config import AppConfig

    # Arrange: forzar SYNC mode (legacy). AppConfig.async_mode es atributo
    # de clase (evaluado en cold start); monkeypatch lo sobrescribe para
    # el alcance del test. El handler lo lee en cada invocacion para
    # decidir success_status, asi que no requiere reimport del modulo.
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
            'message': 'Hola, me interesa colaborar contigo.',
            'cf_token': 'x' * 30,
            'niche': 'fintech',
        },
        ip='203.0.113.30',
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert len(body['contact_id']) == 36
    assert (
        response['headers']['Access-Control-Allow-Origin']
        == 'https://the-full-stack.com'
    )
