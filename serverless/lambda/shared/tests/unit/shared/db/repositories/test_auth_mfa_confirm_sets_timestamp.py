"""
Given un row MFA pendiente (confirmed_at=None),
When se llama confirm_mfa,
Then setea confirmed_at != None y hace flush.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth import AuthMfaKind, AuthMfaMethod
from shared.db.repositories.auth_mfa import confirm_mfa

pytestmark = pytest.mark.unit


def test_confirm_mfa_sets_timestamp():
    # Arrange
    session = MagicMock()
    method = AuthMfaMethod(user_id='u1', kind=AuthMfaKind.TOTP)
    session.execute.return_value.scalar_one_or_none.return_value = method

    # Act
    result = confirm_mfa(session, user_id='u1', kind=AuthMfaKind.TOTP)

    # Assert
    assert result is method
    assert method.confirmed_at is not None
    session.flush.assert_called_once()
