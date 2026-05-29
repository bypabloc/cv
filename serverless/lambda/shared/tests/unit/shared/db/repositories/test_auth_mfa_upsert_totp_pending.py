"""
Given un user sin row TOTP previo,
When se llama upsert_totp_method,
Then inserta un row TOTP nuevo con confirmed_at=None y hace flush.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth import AuthMfaKind
from shared.db.repositories.auth_mfa import upsert_totp_method

pytestmark = pytest.mark.unit


def test_upsert_totp_method_inserts_pending():
    # Arrange — get_mfa_method no encuentra row previo.
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    method = upsert_totp_method(session, user_id='u1', ciphertext=b'ct-bytes')

    # Assert
    assert method.kind == AuthMfaKind.TOTP
    assert method.totp_secret_ciphertext == b'ct-bytes'
    assert method.confirmed_at is None
    session.add.assert_called_once_with(method)
    session.flush.assert_called_once()
