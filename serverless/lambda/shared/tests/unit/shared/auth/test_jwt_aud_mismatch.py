"""
Given un JWT con aud='other',
When se verifica con audience='portfolio' (default),
Then levanta JwtInvalidError por audience mismatch.
"""

from uuid import uuid4

import pytest
from shared.auth import JwtInvalidError, issue_temp_jwt, verify_jwt

pytestmark = pytest.mark.unit


def test_jwt_aud_mismatch_raises_jwt_invalid_error():
    # Arrange
    secret = 'a' * 64
    token, _ = issue_temp_jwt(
        user_id=uuid4(),
        flow='register',
        step=1,
        secret=secret,
        audience='other-audience',
    )

    # Act + Assert (verifica con la audience default 'portfolio')
    with pytest.raises(JwtInvalidError):
        verify_jwt(token, secret=secret)
