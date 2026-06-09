"""shared.crypto.bypass_token — rechaza stage distinto.

Given un token firmado para stage='dev',
When se verifica exigiendo stage='prod',
Then levanta BypassTokenError(code='STAGE_MISMATCH').
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import BypassTokenError
from shared.crypto.bypass_token import sign_bypass_token, verify_bypass_token
from shared.crypto.ed25519 import generate_keypair

pytestmark = pytest.mark.unit


def test_verify_rejects_stage_mismatch() -> None:
    # Arrange
    private_b64, public_b64 = generate_keypair()
    now = 1_700_000_000
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=now,
    )

    # Act / Assert: el Lambda es 'prod', el token dice 'dev'.
    with pytest.raises(BypassTokenError) as exc_info:
        verify_bypass_token(
            token,
            public_key_b64=public_b64,
            stage='prod',
            now=now + 10,
        )

    assert exc_info.value.code == 'STAGE_MISMATCH'
