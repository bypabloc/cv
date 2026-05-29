"""
Given una assertion cuyo sign_count regreso (new <= stored, stored > 0),
When se llama verify_authentication,
Then levanta WebauthnCloneError con el credential_id afectado (clone detection).
"""

from __future__ import annotations

import fido2.cbor as cbor
import pytest
import shared.auth.webauthn as wa


def test_webauthn_login_verify_sign_count_clone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    cred_id = b'cred-clone'
    pk_cbor = cbor.encode(
        {1: 2, 3: -7, -1: 1, -2: b'\x01' * 32, -3: b'\x02' * 32}
    )

    class _FakeMatched:
        credential_id = cred_id

    monkeypatch.setattr(
        wa.Fido2Server,
        'authenticate_complete',
        lambda self, state, creds, response: _FakeMatched(),
    )
    # new=5 <= stored=10 -> regresion -> clone
    monkeypatch.setattr(wa, '_extract_counter', lambda response: 5)

    # Act / Assert
    with pytest.raises(wa.WebauthnCloneError) as exc_info:
        wa.verify_authentication(
            rp_id='example.com',
            rp_name='Test',
            expected_origins=['https://example.com'],
            state={'challenge': 'c', 'user_verification': 'required'},
            response={'id': 'x'},
            stored_credentials=[
                {
                    'credential_id': cred_id,
                    'public_key': pk_cbor,
                    'sign_count': 10,
                },
            ],
        )
    assert exc_info.value.credential_id == cred_id
