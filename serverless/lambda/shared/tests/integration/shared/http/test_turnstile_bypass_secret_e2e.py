"""
Given STAGE=dev, un bypass secret en SSM y cf_response vacio,
When verify_turnstile_token recibe el bypass secret correcto,
Then devuelve un dict bypassed=True sin pegar a Cloudflare.
"""

from __future__ import annotations

import pytest
from moto import mock_aws
from shared.aws.ssm import clear_cache
from shared.http.turnstile import verify_turnstile_token

pytestmark = pytest.mark.integration


@mock_aws
def test_turnstile_bypass_secret_e2e(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cf_response vacio + bypass secret valido en dev -> bypassed=True."""
    # Arrange
    monkeypatch.setenv('STAGE', 'dev')
    monkeypatch.setenv(
        'SSM_TURNSTILE_BYPASS_PATH', '/portfolio/dev/turnstile-bypass-secret'
    )
    import boto3

    boto3.client('ssm', region_name='us-east-1').put_parameter(
        Name='/portfolio/dev/turnstile-bypass-secret',
        Value='e2e-bypass',
        Type='SecureString',
    )
    clear_cache()

    # Act
    result = verify_turnstile_token('', bypass_secret='e2e-bypass')

    # Assert
    assert result['success'] is True
    assert result['bypassed'] is True
