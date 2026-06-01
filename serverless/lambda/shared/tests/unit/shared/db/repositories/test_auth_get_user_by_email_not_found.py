"""
Given una DB sin row para email='missing@x.com',
When se llama get_user_by_email('missing@x.com'),
Then retorna None (sin levantar excepcion).
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth import get_user_by_email

pytestmark = pytest.mark.unit


def test_get_user_by_email_returns_none_when_not_found():
    # Arrange
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    result = get_user_by_email(session, 'missing@x.com')

    # Assert
    assert result is None
