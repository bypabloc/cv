"""
Given los datos de una accion admin,
When se llama insert_admin_action,
Then hace session.add + flush y retorna el row agregado.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import insert_admin_action

pytestmark = pytest.mark.unit


def test_insert_admin_action_adds_and_returns_row():
    # Arrange
    session = MagicMock()

    # Act
    row = insert_admin_action(
        session,
        admin_user_id='admin1',
        target_user_id='u1',
        action='disable',
    )

    # Assert
    assert row.action == 'disable'
    session.add.assert_called_once_with(row)
    session.flush.assert_called_once()
