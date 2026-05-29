"""
Given que el user tiene 7 recovery codes sin consumir,
When se llama count_remaining_recovery_codes (session.scalar),
Then retorna 7.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import count_remaining_recovery_codes

pytestmark = pytest.mark.unit


def test_count_remaining_recovery_codes_returns_count():
    # Arrange
    session = MagicMock()
    session.scalar.return_value = 7

    # Act
    result = count_remaining_recovery_codes(session, user_id='u1')

    # Assert
    assert result == 7
