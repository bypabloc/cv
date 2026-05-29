"""
Given una attestation valida (Fido2Server mockeado en el boundary),
When se llama verify_registration,
Then extrae credential_id + public_key (CBOR) + sign_count + format + transports.
"""

from __future__ import annotations

import fido2.cbor as cbor
import pytest
from shared.auth import webauthn as wa


def test_webauthn_register_verify_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange — el cose key es un mapa EC2/ES256 valido (cbor-encodable).
    cose_key = {1: 2, 3: -7, -1: 1, -2: b'\x01' * 32, -3: b'\x02' * 32}

    class _FakeCred:
        credential_id = b'cred-123'
        public_key = cose_key
        aaguid = b'\x00' * 16

    class _FakeAuthData:
        credential_data = _FakeCred()
        counter = 0

    class _FakeAtt:
        fmt = 'none'

    class _FakeResp:
        attestation_object = _FakeAtt()

    class _FakeReg:
        response = _FakeResp()

    monkeypatch.setattr(
        wa.Fido2Server,
        'register_complete',
        lambda self, state, response: _FakeAuthData(),
    )
    monkeypatch.setattr(
        wa.RegistrationResponse,
        'from_dict',
        staticmethod(lambda data: _FakeReg()),
    )

    # Act
    result = wa.verify_registration(
        rp_id='example.com',
        rp_name='Test',
        expected_origins=['https://example.com'],
        state={'challenge': 'c', 'user_verification': 'preferred'},
        response={'id': 'x', 'response': {'transports': ['internal']}},
    )

    # Assert
    assert result['credential_id'] == b'cred-123'
    assert result['sign_count'] == 0
    assert result['attestation_format'] == 'none'
    assert result['transports'] == ['internal']
    assert result['public_key'] == cbor.encode(cose_key)
