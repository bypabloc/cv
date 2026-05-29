"""
Given un user_id que existe,
When se llama get_user_by_id (session.get),
Then retorna el user encontrado.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import get_user_by_id

pytestmark = pytest.mark.unit


def test_get_user_by_id_returns_user_when_found():
    # Arrange
    session = MagicMock()
    user = MagicMock()
    session.get.return_value = user

    # Act
    result = get_user_by_id(session, user_id='u1')

    # Assert
    assert result is user
