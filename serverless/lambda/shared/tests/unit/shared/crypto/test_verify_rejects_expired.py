"""shared.crypto.bypass_token — rechaza token expirado.

Given un token firmado con exp = now+300,
When se verifica con now posterior a exp,
Then levanta BypassTokenError(code='EXPIRED').
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import BypassTokenError
from shared.crypto.bypass_token import (
    DEFAULT_TTL_SECONDS,
    sign_bypass_token,
    verify_bypass_token,
)
from shared.crypto.ed25519 import generate_keypair

pytestmark = pytest.mark.unit


def test_verify_rejects_expired_token() -> None:
    # Arrange
    private_b64, public_b64 = generate_keypair()
    now = 1_700_000_000
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=now,
    )

    # Act / Assert: now ya supera exp (now + TTL).
    with pytest.raises(BypassTokenError) as exc_info:
        verify_bypass_token(
            token,
            public_key_b64=public_b64,
            stage='dev',
            now=now + DEFAULT_TTL_SECONDS + 1,
        )

    assert exc_info.value.code == 'EXPIRED'


def test_verify_rejects_exactly_at_exp() -> None:
    # Arrange: now == exp es invalido (la ventana es [iat, exp)).
    private_b64, public_b64 = generate_keypair()
    now = 1_700_000_000
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=now,
    )

    # Act / Assert
    with pytest.raises(BypassTokenError) as exc_info:
        verify_bypass_token(
            token,
            public_key_b64=public_b64,
            stage='dev',
            now=now + DEFAULT_TTL_SECONDS,
        )

    assert exc_info.value.code == 'EXPIRED'
