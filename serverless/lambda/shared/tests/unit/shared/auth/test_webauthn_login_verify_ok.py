"""
Given una assertion valida con sign_count creciente (boundary mockeado),
When se llama verify_authentication,
Then retorna el credential_id matcheado + el new_sign_count nuevo.
"""

from __future__ import annotations

import fido2.cbor as cbor
import pytest
import shared.auth.webauthn as wa


def test_webauthn_login_verify_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    cred_id = b'cred-xyz'
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
    monkeypatch.setattr(wa, '_extract_counter', lambda response: 6)

    # Act
    result = wa.verify_authentication(
        rp_id='example.com',
        rp_name='Test',
        expected_origins=['https://example.com'],
        state={'challenge': 'c', 'user_verification': 'required'},
        response={'id': 'x'},
        stored_credentials=[
            {'credential_id': cred_id, 'public_key': pk_cbor, 'sign_count': 5},
        ],
    )

    # Assert
    assert result == {'credential_id': cred_id, 'new_sign_count': 6}
