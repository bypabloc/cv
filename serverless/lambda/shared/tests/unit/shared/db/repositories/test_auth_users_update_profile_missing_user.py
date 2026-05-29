"""
Given un user_id que no existe,
When se llama update_profile (session.get retorna None),
Then retorna None sin hacer flush.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import update_profile

pytestmark = pytest.mark.unit


def test_update_profile_returns_none_when_user_missing():
    # Arrange
    session = MagicMock()
    session.get.return_value = None

    # Act
    result = update_profile(session, user_id='missing', display_name='X')

    # Assert
    assert result is None
    session.flush.assert_not_called()
