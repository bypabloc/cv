"""
Given que no existe sesion del user con ese id,
When se llama revoke_session (scalar_one_or_none None),
Then retorna None sin borrar.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import revoke_session

pytestmark = pytest.mark.unit


def test_revoke_session_returns_none_when_missing():
    # Arrange
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    result = revoke_session(session, user_id='u1', session_id='s1')

    # Assert
    assert result is None
    session.delete.assert_not_called()
