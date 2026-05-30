"""
Given STAGE=dev, la clave PUBLICA del bypass en SSM y cf_response vacio,
When verify_captcha_or_bypass recibe un token Ed25519 firmado valido,
Then devuelve un dict bypassed=True sin pegar a Cloudflare.

E2E del orquestador con SSM real (moto): resuelve la clave PUBLICA del
parametro String y verifica la firma del token emitido por el firmante
(shared.crypto.bypass_token).
"""

from __future__ import annotations

import time

import pytest
from moto import mock_aws
from shared.aws.ssm import clear_cache
from shared.crypto.bypass_token import sign_bypass_token
from shared.crypto.captcha import verify_captcha_or_bypass
from shared.crypto.ed25519 import generate_keypair

pytestmark = pytest.mark.integration


@mock_aws
def test_captcha_bypass_token_e2e(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cf_response vacio + token firmado valido en dev -> bypassed=True."""
    # Arrange: par Ed25519; la publica va a SSM (String), la privada firma.
    private_b64, public_b64 = generate_keypair()
    monkeypatch.setenv('STAGE', 'dev')
    monkeypatch.setenv(
        'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH',
        '/portfolio/dev/turnstile-bypass-public-key',
    )
    import boto3

    boto3.client('ssm', region_name='us-east-1').put_parameter(
        Name='/portfolio/dev/turnstile-bypass-public-key',
        Value=public_b64,
        Type='String',
    )
    clear_cache()

    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=int(time.time()),
    )

    # Act
    result = verify_captcha_or_bypass('', bypass_token=token, stage='dev')

    # Assert
    assert result['success'] is True
    assert result['bypassed'] is True


@mock_aws
def test_captcha_bypass_token_wrong_key_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Token firmado con otra privada -> CAPTCHA_INVALID (firma no matchea)."""
    from shared.core.exceptions import TurnstileError

    private_b64, _ = generate_keypair()
    _, other_public_b64 = generate_keypair()
    monkeypatch.setenv('STAGE', 'dev')
    monkeypatch.setenv(
        'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH',
        '/portfolio/dev/turnstile-bypass-public-key',
    )
    import boto3

    boto3.client('ssm', region_name='us-east-1').put_parameter(
        Name='/portfolio/dev/turnstile-bypass-public-key',
        Value=other_public_b64,
        Type='String',
    )
    clear_cache()

    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=int(time.time()),
    )

    with pytest.raises(TurnstileError) as exc_info:
        verify_captcha_or_bypass('', bypass_token=token, stage='dev')

    assert exc_info.value.code == 'CAPTCHA_INVALID'
