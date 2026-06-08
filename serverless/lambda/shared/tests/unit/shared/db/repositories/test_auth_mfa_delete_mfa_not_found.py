"""
Given que el user no tiene el metodo (row None),
When se llama delete_mfa,
Then NO borra nada y retorna False (anti-enumeration en el controller -> 404).
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthMfaKind
from shared.db.repositories.auth_mfa import delete_mfa

pytestmark = pytest.mark.unit


def test_delete_mfa_returns_false_when_missing():
    # Arrange
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    ok = delete_mfa(session, user_id='u1', kind=AuthMfaKind.TOTP)

    # Assert
    assert ok is False
    session.delete.assert_not_called()
    session.flush.assert_not_called()
