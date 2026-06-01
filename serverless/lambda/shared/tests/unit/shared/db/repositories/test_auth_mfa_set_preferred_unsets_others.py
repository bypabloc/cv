"""
Given dos metodos MFA activos (totp preferred, email_code no),
When se llama set_preferred(kind=email_code),
Then totp.preferred=False y email_code.preferred=True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthMfaKind
from shared.db.models.auth.mfa_method import AuthMfaMethod
from shared.db.repositories.auth_mfa import set_preferred

pytestmark = pytest.mark.unit


def test_set_preferred_unsets_others():
    # Arrange
    session = MagicMock()
    totp = AuthMfaMethod(user_id='u1', kind=AuthMfaKind.TOTP, preferred=True)
    email = AuthMfaMethod(
        user_id='u1',
        kind=AuthMfaKind.EMAIL_CODE,
        preferred=False,
    )
    session.execute.return_value.scalars.return_value = [totp, email]

    # Act
    set_preferred(session, user_id='u1', kind=AuthMfaKind.EMAIL_CODE)

    # Assert
    assert totp.preferred is False
    assert email.preferred is True
    session.flush.assert_called_once()
