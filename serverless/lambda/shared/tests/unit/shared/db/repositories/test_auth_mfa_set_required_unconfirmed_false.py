"""
Given un row MFA activo pero NO confirmado (confirmed_at IS NULL),
When se llama set_required con required=True,
Then NO marca required (un metodo no confirmado no es usable en el login) y
    retorna False (el controller lo traduce a 404).
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthMfaKind
from shared.db.models.auth.mfa_method import AuthMfaMethod
from shared.db.repositories.auth_mfa import set_required

pytestmark = pytest.mark.unit


def test_set_required_unconfirmed_returns_false_and_keeps_flag():
    # Arrange
    session = MagicMock()
    method = AuthMfaMethod(
        user_id='u1',
        kind=AuthMfaKind.TOTP,
        confirmed_at=None,
        required=False,
    )
    session.execute.return_value.scalar_one_or_none.return_value = method

    # Act
    ok = set_required(
        session, user_id='u1', kind=AuthMfaKind.TOTP, required=True,
    )

    # Assert
    assert ok is False
    assert method.required is False
    session.flush.assert_not_called()
