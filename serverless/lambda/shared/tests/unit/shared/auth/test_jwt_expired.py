"""
Given un JWT cuyo exp < now,
When se verifica,
Then levanta JwtExpiredError.
"""

from uuid import uuid4

import pytest
from freezegun import freeze_time

from shared.auth import JwtExpiredError, issue_temp_jwt, verify_jwt


pytestmark = pytest.mark.unit


def test_jwt_expired_raises_jwt_expired_error():
    # Arrange
    secret = 'a' * 64
    with freeze_time('2026-05-28 10:00:00'):
        token, _ = issue_temp_jwt(
            user_id=uuid4(), flow='register', step=1, secret=secret,
        )

    # Act + Assert (10 min despues; el temp expira en 5 min)
    with freeze_time('2026-05-28 10:10:00'):
        with pytest.raises(JwtExpiredError):
            verify_jwt(token, secret=secret)
