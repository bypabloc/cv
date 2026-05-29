"""
Given un user existente,
When se llama hard_delete_user,
Then borra el row del user (session.delete) y retorna True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import hard_delete_user

pytestmark = pytest.mark.unit


def test_hard_delete_user_deletes_and_returns_true():
    # Arrange
    session = MagicMock()
    user = MagicMock()
    session.get.return_value = user

    # Act
    result = hard_delete_user(session, user_id='u1')

    # Assert
    assert result is True
    session.delete.assert_called_once_with(user)
    session.flush.assert_called_once()
