"""
Given que no existe sesion para la family,
When se llama update_session_activity (scalar_one_or_none None),
Then retorna False sin hacer flush.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import update_session_activity

pytestmark = pytest.mark.unit


def test_update_session_activity_returns_false_when_missing():
    # Arrange
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    result = update_session_activity(session, family_id='fam1')

    # Assert
    assert result is False
    session.flush.assert_not_called()
