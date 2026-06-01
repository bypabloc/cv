"""
Given un credential WebAuthn del user,
When se llama delete_webauthn_credential con su record_id,
Then se borra el row y retorna True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.webauthn_credential import AuthWebauthnCredential
from shared.db.repositories.auth_mfa import delete_webauthn_credential

pytestmark = pytest.mark.unit


def test_delete_webauthn_credential_returns_true_if_found():
    # Arrange
    session = MagicMock()
    cred = AuthWebauthnCredential(
        user_id='u1',
        credential_id=b'cid',
        public_key=b'pk',
        sign_count=0,
    )
    session.execute.return_value.scalar_one_or_none.return_value = cred

    # Act
    ok = delete_webauthn_credential(session, user_id='u1', record_id='rec-1')

    # Assert
    assert ok is True
    session.delete.assert_called_once_with(cred)
    session.flush.assert_called_once()
