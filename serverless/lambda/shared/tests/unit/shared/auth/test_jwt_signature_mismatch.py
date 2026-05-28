"""
Given un JWT firmado con secret 'A',
When se verifica con secret 'B',
Then levanta JwtInvalidError por signature mismatch.
"""

from uuid import uuid4

import pytest

from shared.auth import JwtInvalidError, issue_temp_jwt, verify_jwt


pytestmark = pytest.mark.unit


def test_jwt_signature_mismatch_raises_jwt_invalid_error():
    # Arrange
    token, _ = issue_temp_jwt(
        user_id=uuid4(), flow='register', step=1, secret='a' * 64,
    )

    # Act + Assert
    with pytest.raises(JwtInvalidError):
        verify_jwt(token, secret='b' * 64)
