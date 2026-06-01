"""
Given una sesion existente para una family,
When se llama update_session_activity,
Then setea last_active_at, hace flush y retorna True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import update_session_activity

pytestmark = pytest.mark.unit


def test_update_session_activity_returns_true_when_found():
    # Arrange
    session = MagicMock()
    row = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = row

    # Act
    result = update_session_activity(session, family_id='fam1')

    # Assert
    assert result is True
    assert row.last_active_at is not None
    session.flush.assert_called_once()
