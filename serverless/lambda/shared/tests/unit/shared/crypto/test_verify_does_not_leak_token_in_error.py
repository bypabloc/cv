"""shared.crypto.bypass_token — el error NO filtra el token.

Given un token con firma invalida,
When verify_bypass_token levanta BypassTokenError,
Then ni el message ni el extra del error contienen el token (defensa:
     no filtrar el valor del token en logs).
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import BypassTokenError
from shared.crypto.bypass_token import sign_bypass_token, verify_bypass_token
from shared.crypto.ed25519 import generate_keypair

pytestmark = pytest.mark.unit


def test_error_does_not_contain_token_value() -> None:
    # Arrange: token firmado con una clave, verificado con otra publica.
    private_b64, _ = generate_keypair()
    _, other_public_b64 = generate_keypair()
    now = 1_700_000_000
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=now,
    )

    # Act
    with pytest.raises(BypassTokenError) as exc_info:
        verify_bypass_token(
            token,
            public_key_b64=other_public_b64,
            stage='dev',
            now=now + 10,
        )

    # Assert: el token completo NO aparece en el mensaje ni en extra.
    err = exc_info.value
    assert token not in err.message
    assert token not in str(err.extra)
