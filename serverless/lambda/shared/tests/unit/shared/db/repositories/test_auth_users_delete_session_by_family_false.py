"""
Given que no existe sesion para la family,
When se llama delete_session_by_family (scalar_one_or_none None),
Then retorna False sin borrar.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import delete_session_by_family

pytestmark = pytest.mark.unit


def test_delete_session_by_family_returns_false_when_missing():
    # Arrange
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    result = delete_session_by_family(session, family_id='fam1')

    # Assert
    assert result is False
    session.delete.assert_not_called()
