"""shared.crypto.bypass_token — rechaza tokens malformados (controlado).

Given tokens estructuralmente invalidos (vacio, sin punto, b64 roto,
     JSON no-dict, version equivocada),
When se verifican,
Then levantan BypassTokenError con el code esperado, NUNCA una excepcion
     no controlada.
"""

from __future__ import annotations

import json

import pytest
from shared.core.exceptions import BypassTokenError
from shared.crypto.bypass_token import verify_bypass_token
from shared.crypto.ed25519 import (
    _b64url_encode,
    generate_keypair,
    sign_message,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    'bad_token',
    [
        '',
        'no-dot-segment',
        'only.',
        '.only',
        'a.b.c',
        '@@@.@@@',
    ],
)
def test_verify_rejects_structurally_invalid_token(bad_token: str) -> None:
    # Arrange
    _, public_b64 = generate_keypair()

    # Act / Assert: cualquier forma invalida -> MALFORMED o BAD_SIGNATURE,
    # NUNCA una excepcion no controlada.
    with pytest.raises(BypassTokenError) as exc_info:
        verify_bypass_token(
            bad_token,
            public_key_b64=public_b64,
            stage='dev',
            now=1_700_000_000,
        )

    assert exc_info.value.code in ('MALFORMED', 'BAD_SIGNATURE')


def test_verify_rejects_unsupported_version() -> None:
    # Arrange: payload con version equivocada, FIRMADO correctamente
    # (para pasar la firma y llegar al check de version).
    private_b64, public_b64 = generate_keypair()
    payload = {
        'v': 999,
        'iat': 1_700_000_000,
        'exp': 1_700_000_300,
        'jti': 'deadbeef',
        'stage': 'dev',
    }
    payload_seg = _b64url_encode(
        json.dumps(payload, sort_keys=True, separators=(',', ':')).encode(),
    )
    sig = sign_message(private_b64, payload_seg.encode('ascii'))
    token = f'{payload_seg}.{_b64url_encode(sig)}'

    # Act / Assert
    with pytest.raises(BypassTokenError) as exc_info:
        verify_bypass_token(
            token,
            public_key_b64=public_b64,
            stage='dev',
            now=1_700_000_010,
        )

    assert exc_info.value.code == 'BAD_VERSION'


def test_verify_rejects_non_dict_payload() -> None:
    # Arrange: payload JSON valido pero NO un objeto (una lista), firmado
    # correctamente.
    private_b64, public_b64 = generate_keypair()
    payload_seg = _b64url_encode(json.dumps([1, 2, 3]).encode())
    sig = sign_message(private_b64, payload_seg.encode('ascii'))
    token = f'{payload_seg}.{_b64url_encode(sig)}'

    # Act / Assert
    with pytest.raises(BypassTokenError) as exc_info:
        verify_bypass_token(
            token,
            public_key_b64=public_b64,
            stage='dev',
            now=1_700_000_010,
        )

    assert exc_info.value.code == 'MALFORMED'
