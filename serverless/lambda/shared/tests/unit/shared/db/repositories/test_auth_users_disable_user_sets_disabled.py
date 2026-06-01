"""
Given un user activo (deleted_at None),
When se llama disable_user,
Then status=DISABLED y retorna True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthUserStatus
from shared.db.repositories.auth_users import disable_user

pytestmark = pytest.mark.unit


def test_disable_user_sets_status_disabled():
    # Arrange
    session = MagicMock()
    user = MagicMock()
    user.deleted_at = None
    session.get.return_value = user

    # Act
    result = disable_user(session, user_id='u1')

    # Assert
    assert result is True
    assert user.status == AuthUserStatus.DISABLED
    session.flush.assert_called_once()
