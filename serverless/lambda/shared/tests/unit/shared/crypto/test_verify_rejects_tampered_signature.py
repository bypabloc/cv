"""shared.crypto.bypass_token — rechaza firma alterada.

Given un token firmado al que se le altera 1 caracter de la firma,
When se verifica con la publica correcta,
Then levanta BypassTokenError(code='BAD_SIGNATURE').
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import BypassTokenError
from shared.crypto.bypass_token import sign_bypass_token, verify_bypass_token
from shared.crypto.ed25519 import generate_keypair

pytestmark = pytest.mark.unit


def test_verify_rejects_tampered_signature() -> None:
    # Arrange
    private_b64, public_b64 = generate_keypair()
    now = 1_700_000_000
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=now,
    )
    payload_seg, sig_seg = token.split('.')
    # Flip del primer caracter de la firma (A<->B) para alterarla.
    flipped = ('B' if sig_seg[0] != 'B' else 'A') + sig_seg[1:]
    tampered = f'{payload_seg}.{flipped}'

    # Act / Assert
    with pytest.raises(BypassTokenError) as exc_info:
        verify_bypass_token(
            tampered,
            public_key_b64=public_b64,
            stage='dev',
            now=now + 10,
        )

    assert exc_info.value.code == 'BAD_SIGNATURE'


def test_verify_rejects_wrong_public_key() -> None:
    # Arrange: firmado con una clave, verificado con OTRA publica.
    private_b64, _ = generate_keypair()
    _, other_public_b64 = generate_keypair()
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
            public_key_b64=other_public_b64,
            stage='dev',
            now=now + 10,
        )

    assert exc_info.value.code == 'BAD_SIGNATURE'
