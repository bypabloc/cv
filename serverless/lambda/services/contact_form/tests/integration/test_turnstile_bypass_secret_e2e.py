"""Integration E2E — bypass de Turnstile via secret header en dev.

Given un evento API Gateway con `cf_token` vacio y el header
     `X-Turnstile-Bypass-Secret` que coincide con el secret SSM, en
     STAGE=dev,
When se invoca el `lambda_handler` end-to-end,
Then el bypass aplica (no se llama a Cloudflare siteverify), devuelve
     HTTP 201 y el contacto queda persistido en DynamoDB.
"""

import json

import boto3
import pytest

from tests.integration._fixtures import (
    _api_gw_event,
    _get_contact,
    _lambda_context,
    _valid_body,
)

pytestmark = pytest.mark.integration


def test_turnstile_bypass_secret_e2e(aws_env, monkeypatch):
    import handler

    # Arrange: STAGE=dev habilita el bypass; el secret vive en SSM y el
    # header del request debe coincidir. cf_token vacio activa la rama
    # de bypass en verify_turnstile_token (no se contacta a Cloudflare).
    monkeypatch.setenv('STAGE', 'dev')
    monkeypatch.setenv(
        'SSM_TURNSTILE_BYPASS_SECRET_PATH',
        '/portfolio-test/turnstile-bypass',
    )
    ssm = boto3.client('ssm', region_name='us-east-1')
    ssm.put_parameter(
        Name='/portfolio-test/turnstile-bypass',
        Value='dev-bypass-secret',
        Type='SecureString',
    )
    event = _api_gw_event(
        body=_valid_body(cf_token=''),
        ip='198.51.100.28',
        extra_headers={'X-Turnstile-Bypass-Secret': 'dev-bypass-secret'},
    )

    # Act
    response = handler.lambda_handler(event, _lambda_context())

    # Assert
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    item = _get_contact(body['contact_id'])
    assert item['name'] == 'Pablo Contreras'
