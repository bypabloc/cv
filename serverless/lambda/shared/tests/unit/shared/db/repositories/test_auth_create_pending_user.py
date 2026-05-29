"""
Given un email lowercased,
When se llama create_pending_user,
Then se inserta un AuthUser con status=pending y se hace flush().
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth import AuthUserStatus
from shared.db.repositories.auth import create_pending_user

pytestmark = pytest.mark.unit


def test_create_pending_user_adds_and_flushes():
    # Arrange
    session = MagicMock()

    # Act
    user = create_pending_user(session, email='new@x.com')

    # Assert
    assert user.email == 'new@x.com'
    assert user.status == AuthUserStatus.PENDING
    session.add.assert_called_once_with(user)
    session.flush.assert_called_once()
