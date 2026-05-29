"""
Given que el user tiene 3 sesiones activas,
When se llama count_user_sessions (session.scalar),
Then retorna 3.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import count_user_sessions

pytestmark = pytest.mark.unit


def test_count_user_sessions_returns_count():
    # Arrange
    session = MagicMock()
    session.scalar.return_value = 3

    # Act
    result = count_user_sessions(session, user_id='u1')

    # Assert
    assert result == 3
