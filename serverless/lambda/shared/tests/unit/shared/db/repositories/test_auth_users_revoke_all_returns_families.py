"""
Given que el user tiene varias sesiones,
When se llama revoke_all_user_sessions,
Then retorna los family_id borrados (scalars list).
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import revoke_all_user_sessions

pytestmark = pytest.mark.unit


def test_revoke_all_user_sessions_returns_family_list():
    # Arrange
    session = MagicMock()
    session.execute.return_value.scalars.return_value = ['f1', 'f2']

    # Act
    result = revoke_all_user_sessions(session, user_id='u1')

    # Assert
    assert result == ['f1', 'f2']
    session.flush.assert_called_once()
