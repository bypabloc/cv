"""
Given una sesion existente para una family,
When se llama delete_session_by_family,
Then borra el row (session.delete) y retorna True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import delete_session_by_family

pytestmark = pytest.mark.unit


def test_delete_session_by_family_returns_true_when_found():
    # Arrange
    session = MagicMock()
    row = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = row

    # Act
    result = delete_session_by_family(session, family_id='fam1')

    # Assert
    assert result is True
    session.delete.assert_called_once_with(row)
    session.flush.assert_called_once()
