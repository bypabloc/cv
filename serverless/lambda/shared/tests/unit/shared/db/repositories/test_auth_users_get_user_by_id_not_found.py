"""
Given un user_id que no existe,
When se llama get_user_by_id (session.get retorna None),
Then retorna None.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import get_user_by_id

pytestmark = pytest.mark.unit


def test_get_user_by_id_returns_none_when_not_found():
    # Arrange
    session = MagicMock()
    session.get.return_value = None

    # Act
    result = get_user_by_id(session, user_id='missing')

    # Assert
    assert result is None
