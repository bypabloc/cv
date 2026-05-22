"""
Given un Turnstile secret en SSM y un siteverify que responde success,
When verify_turnstile_token valida un token,
Then httpx pega al endpoint real (mockeado) y devuelve la respuesta.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from moto import mock_aws
from shared.aws.ssm import clear_cache
from shared.http.turnstile import (
    TURNSTILE_SITEVERIFY_URL,
    verify_turnstile_token,
)

pytestmark = pytest.mark.integration


@mock_aws
@respx.mock
def test_turnstile_valid_token_e2e() -> None:
    """Token valido -> siteverify responde success -> verify devuelve dict."""
    # Arrange
    import boto3

    boto3.client('ssm', region_name='us-east-1').put_parameter(
        Name='/portfolio/turnstile-secret',
        Value='0xSECRET',
        Type='SecureString',
    )
    clear_cache()
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'localhost'}
        )
    )

    # Act
    result = verify_turnstile_token('cf-token-abc', remote_ip='1.2.3.4')

    # Assert
    assert result['success'] is True
    assert result['hostname'] == 'localhost'
