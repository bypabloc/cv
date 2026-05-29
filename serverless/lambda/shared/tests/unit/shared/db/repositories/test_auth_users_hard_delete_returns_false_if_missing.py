"""
Given un user_id que no existe,
When se llama hard_delete_user (session.get retorna None),
Then retorna False sin borrar.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import hard_delete_user

pytestmark = pytest.mark.unit


def test_hard_delete_user_returns_false_when_missing():
    # Arrange
    session = MagicMock()
    session.get.return_value = None

    # Act
    result = hard_delete_user(session, user_id='missing')

    # Assert
    assert result is False
    session.delete.assert_not_called()
