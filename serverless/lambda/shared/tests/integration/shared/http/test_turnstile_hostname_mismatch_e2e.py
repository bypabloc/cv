"""
Given un siteverify que responde success pero con un hostname no permitido,
When verify_turnstile_token valida el token en STAGE != dev,
Then levanta TurnstileError con code CAPTCHA_HOSTNAME_MISMATCH.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from moto import mock_aws
from shared.aws.ssm import clear_cache
from shared.core.exceptions import TurnstileError
from shared.http.turnstile import (
    TURNSTILE_SITEVERIFY_URL,
    verify_turnstile_token,
)

pytestmark = pytest.mark.integration


@mock_aws
@respx.mock
def test_turnstile_hostname_mismatch_e2e(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """hostname fuera de la whitelist -> CAPTCHA_HOSTNAME_MISMATCH."""
    # Arrange: STAGE=prod (no *.localhost) y CORS sin el host atacante.
    monkeypatch.setenv('STAGE', 'prod')
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', 'https://the-full-stack.com')
    import boto3

    boto3.client('ssm', region_name='us-east-1').put_parameter(
        Name='/portfolio/turnstile-secret',
        Value='0xSECRET',
        Type='SecureString',
    )
    clear_cache()
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200,
            json={'success': True, 'hostname': 'attacker.example.com'},
        )
    )

    # Act / Assert
    with pytest.raises(TurnstileError) as exc_info:
        verify_turnstile_token('cf-token', remote_ip='1.2.3.4')
    assert exc_info.value.code == 'CAPTCHA_HOSTNAME_MISMATCH'
