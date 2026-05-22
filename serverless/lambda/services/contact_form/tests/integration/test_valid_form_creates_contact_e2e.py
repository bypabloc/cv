"""Integration E2E — form valido + Turnstile OK persiste y notifica.

Given un evento API Gateway crudo con un form valido y Turnstile
     siteverify respondiendo success=true,
When se invoca el `lambda_handler` end-to-end,
Then devuelve HTTP 201 con `contact_id` + `created_at`, el contacto
     queda persistido en DynamoDB y SES registra el email enviado.
"""

import json

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.integration._fixtures import (
    _api_gw_event,
    _get_contact,
    _lambda_context,
    _ses_last_email,
    _ses_sent_count,
    _valid_body,
)

pytestmark = pytest.mark.integration


@respx.mock
def test_valid_form_creates_contact_e2e(aws_env):
    import handler

    # Arrange
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    event = _api_gw_event(
        body=_valid_body(name='Pablo Contreras', niche='fintech'),
        ip='198.51.100.20',
    )

    # Act
    response = handler.lambda_handler(event, _lambda_context())

    # Assert
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert len(body['contact_id']) == 36
    assert body['created_at'].endswith('+00:00')

    item = _get_contact(body['contact_id'])
    assert item['name'] == 'Pablo Contreras'
    assert item['email'] == 'user@example.com'
    assert item['niche'] == 'fintech'

    assert _ses_sent_count() == 1
    email = _ses_last_email()
    assert email.destinations == {'ToAddresses': ['owner@example.com']}
