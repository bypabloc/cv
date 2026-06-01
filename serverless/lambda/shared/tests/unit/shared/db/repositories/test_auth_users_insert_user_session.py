"""
Given los datos de una sesion activa,
When se llama insert_user_session,
Then hace session.add + flush y retorna el row agregado.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import insert_user_session

pytestmark = pytest.mark.unit


def test_insert_user_session_adds_and_returns_row():
    # Arrange
    session = MagicMock()

    # Act
    row = insert_user_session(session, user_id='u1', family_id='fam1')

    # Assert
    assert row.user_id == 'u1'
    assert row.family_id == 'fam1'
    session.add.assert_called_once_with(row)
    session.flush.assert_called_once()
