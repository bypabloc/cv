"""
Given un siteverify que responde success=false con error-codes,
When verify_turnstile_token valida el token,
Then levanta TurnstileError con code CAPTCHA_INVALID.
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
def test_turnstile_invalid_token_e2e() -> None:
    """siteverify success=false -> TurnstileError CAPTCHA_INVALID."""
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
            200,
            json={
                'success': False,
                'error-codes': ['invalid-input-response'],
            },
        )
    )

    # Act / Assert
    with pytest.raises(TurnstileError) as exc_info:
        verify_turnstile_token('bad-token', remote_ip='1.2.3.4')
    assert exc_info.value.code == 'CAPTCHA_INVALID'
