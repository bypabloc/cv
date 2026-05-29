"""
Given los datos de un credential WebAuthn validado,
When se llama insert_webauthn_credential,
Then se hace add del row y flush, retornando el credential.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_mfa import insert_webauthn_credential

pytestmark = pytest.mark.unit


def test_insert_webauthn_credential_adds_row():
    # Arrange
    session = MagicMock()

    # Act
    cred = insert_webauthn_credential(
        session,
        user_id='u1',
        credential_id=b'cred-id',
        public_key=b'pk-bytes',
        sign_count=0,
        transports=['internal'],
        attestation_format='none',
        aaguid='00000000-0000-0000-0000-000000000000',
        nickname='Yubikey',
    )

    # Assert
    assert cred.credential_id == b'cred-id'
    assert cred.sign_count == 0
    session.add.assert_called_once_with(cred)
    session.flush.assert_called_once()
