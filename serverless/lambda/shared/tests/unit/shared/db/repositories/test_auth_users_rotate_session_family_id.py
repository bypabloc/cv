"""
Given una sesion existente con un family_id viejo,
When se llama rotate_session_family_id,
Then setea family_id al nuevo, hace flush y retorna True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import rotate_session_family_id

pytestmark = pytest.mark.unit


def test_rotate_session_family_id_sets_new_family():
    # Arrange
    session = MagicMock()
    row = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = row

    # Act
    result = rotate_session_family_id(
        session, old_family_id='old', new_family_id='new',
    )

    # Assert
    assert result is True
    assert row.family_id == 'new'
    session.flush.assert_called_once()
