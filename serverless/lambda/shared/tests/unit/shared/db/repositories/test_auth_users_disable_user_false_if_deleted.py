"""
Given un user ya borrado (deleted_at seteado),
When se llama disable_user,
Then retorna False sin hacer flush.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import disable_user

pytestmark = pytest.mark.unit


def test_disable_user_returns_false_when_deleted():
    # Arrange
    session = MagicMock()
    user = MagicMock()
    user.deleted_at = datetime(2026, 5, 28, 12, 0, 0, tzinfo=UTC)
    session.get.return_value = user

    # Act
    result = disable_user(session, user_id='u1')

    # Assert
    assert result is False
    session.flush.assert_not_called()
