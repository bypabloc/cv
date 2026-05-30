"""
Given un row MFA activo,
When se llama disable_mfa,
Then setea disabled_at != None, preferred=False y retorna True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthMfaKind
from shared.db.models.auth.mfa_method import AuthMfaMethod
from shared.db.repositories.auth_mfa import disable_mfa

pytestmark = pytest.mark.unit


def test_disable_mfa_sets_disabled_at():
    # Arrange
    session = MagicMock()
    method = AuthMfaMethod(user_id='u1', kind=AuthMfaKind.TOTP, preferred=True)
    session.execute.return_value.scalar_one_or_none.return_value = method

    # Act
    ok = disable_mfa(session, user_id='u1', kind=AuthMfaKind.TOTP)

    # Assert
    assert ok is True
    assert method.disabled_at is not None
    assert method.preferred is False
    session.flush.assert_called_once()
