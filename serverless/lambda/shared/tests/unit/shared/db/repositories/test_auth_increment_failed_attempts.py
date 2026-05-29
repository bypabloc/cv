"""
Given un AuthUser con failed_attempts=4,
When se llama increment_failed_attempts,
Then el contador queda en 5 y se retorna 5.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth import AuthUser, AuthUserStatus
from shared.db.repositories.auth import increment_failed_attempts

pytestmark = pytest.mark.unit


def test_increment_failed_attempts_returns_new_value():
    # Arrange
    session = MagicMock()
    user = AuthUser(
        id='01900000-0000-7000-8000-000000000001',
        email='u@x.com',
        status=AuthUserStatus.ACTIVE,
        failed_attempts=4,
    )

    # Act
    result = increment_failed_attempts(session, user)

    # Assert
    assert result == 5
    assert user.failed_attempts == 5
    session.flush.assert_called_once()
