"""
Given una sesion del user (dual filter matchea),
When se llama revoke_session,
Then borra el row (session.delete) y retorna su family_id.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import revoke_session

pytestmark = pytest.mark.unit


def test_revoke_session_deletes_and_returns_family():
    # Arrange
    session = MagicMock()
    row = MagicMock()
    row.family_id = 'fam'
    session.execute.return_value.scalar_one_or_none.return_value = row

    # Act
    result = revoke_session(session, user_id='u1', session_id='s1')

    # Assert
    assert result == 'fam'
    session.delete.assert_called_once_with(row)
    session.flush.assert_called_once()
