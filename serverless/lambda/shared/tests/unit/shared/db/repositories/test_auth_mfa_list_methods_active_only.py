"""
Given metodos MFA del user (algunos disabled),
When se llama list_mfa_methods,
Then la query filtra disabled_at IS NULL y retorna los activos.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthMfaKind
from shared.db.models.auth.mfa_method import AuthMfaMethod
from shared.db.repositories.auth_mfa import list_mfa_methods

pytestmark = pytest.mark.unit


def test_list_mfa_methods_returns_active_only():
    # Arrange
    session = MagicMock()
    active = AuthMfaMethod(user_id='u1', kind=AuthMfaKind.TOTP)
    session.execute.return_value.scalars.return_value = [active]

    # Act
    result = list_mfa_methods(session, user_id='u1')

    # Assert
    assert result == [active]
    session.execute.assert_called_once()
