"""Integration E2E — el email falla pero el contacto se persiste igual.

Given que el remitente SES configurado en SSM NO esta verificado (SES
     rechaza el `send_email` con MessageRejected),
When se invoca el `lambda_handler` end-to-end con un form valido,
Then devuelve HTTP 201 igual y el contacto queda persistido en DynamoDB
     (el lead no se pierde por un fallo de notificacion).
"""

import json

import boto3
import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

from tests.integration._fixtures import (
    _api_gw_event,
    _get_contact,
    _lambda_context,
    _valid_body,
)

pytestmark = pytest.mark.integration


@respx.mock
def test_email_failure_still_persists_e2e(aws_env):
    import handler

    # Arrange: el remitente SSM apunta a un dominio NO verificado en SES.
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )
    ssm = boto3.client('ssm', region_name='us-east-1')
    ssm.put_parameter(
        Name='/portfolio-test/ses-from-address',
        Value='no-reply@unverified-domain.com',
        Type='String',
        Overwrite=True,
    )
    event = _api_gw_event(body=_valid_body(name='Lead Importante'), ip='198.51.100.27')

    # Act
    response = handler.lambda_handler(event, _lambda_context())

    # Assert
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    item = _get_contact(body['contact_id'])
    assert item['name'] == 'Lead Importante'
