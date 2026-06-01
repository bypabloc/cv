"""shared.crypto.bypass_token — roundtrip firma + verificacion.

Given un par Ed25519 y un token firmado para stage='dev' valido 300s,
When se verifica con la publica correspondiente y el mismo stage,
Then retorna el payload con los claims esperados (v, stage, exp).
"""

from __future__ import annotations

import pytest
from shared.crypto.bypass_token import (
    DEFAULT_TTL_SECONDS,
    TOKEN_VERSION,
    sign_bypass_token,
    verify_bypass_token,
)
from shared.crypto.ed25519 import generate_keypair

pytestmark = pytest.mark.unit


def test_sign_and_verify_roundtrip_returns_payload() -> None:
    # Arrange
    private_b64, public_b64 = generate_keypair()
    now = 1_700_000_000

    # Act
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=now,
    )
    payload = verify_bypass_token(
        token,
        public_key_b64=public_b64,
        stage='dev',
        now=now + 10,
    )

    # Assert
    assert payload['v'] == TOKEN_VERSION
    assert payload['stage'] == 'dev'
    assert payload['iat'] == now
    assert payload['exp'] == now + DEFAULT_TTL_SECONDS
