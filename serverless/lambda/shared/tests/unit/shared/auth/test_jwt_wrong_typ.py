"""
Given un JWT temp valido,
When se verifica con expected_typ='access',
Then levanta JwtInvalidError por mismatch de typ.
"""

from uuid import uuid4

import pytest

from shared.auth import JwtInvalidError, issue_temp_jwt, verify_jwt


pytestmark = pytest.mark.unit


def test_jwt_wrong_typ_raises_jwt_invalid_error():
    # Arrange
    secret = 'a' * 64
    token, _ = issue_temp_jwt(
        user_id=uuid4(), flow='register', step=1, secret=secret,
    )

    # Act + Assert
    with pytest.raises(JwtInvalidError, match='typ mismatch'):
        verify_jwt(token, secret=secret, expected_typ='access')
