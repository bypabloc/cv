"""
Given un row MFA del user,
When se llama delete_mfa,
Then borra el row (session.delete) y retorna True (hard-delete, no soft).
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthMfaKind
from shared.db.models.auth.mfa_method import AuthMfaMethod
from shared.db.repositories.auth_mfa import delete_mfa

pytestmark = pytest.mark.unit


def test_delete_mfa_deletes_row():
    # Arrange
    session = MagicMock()
    method = AuthMfaMethod(user_id='u1', kind=AuthMfaKind.TOTP)
    session.execute.return_value.scalar_one_or_none.return_value = method

    # Act
    ok = delete_mfa(session, user_id='u1', kind=AuthMfaKind.TOTP)

    # Assert
    assert ok is True
    session.delete.assert_called_once_with(method)
    session.flush.assert_called_once()
