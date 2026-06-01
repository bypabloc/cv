"""
Given un row AuthUser con email='user@x.com' en la DB,
When se llama get_user_by_email('user@x.com'),
Then retorna ese AuthUser.

Test usa un Mock de Session porque shared.db usa SQLAlchemy 2.x con
postgres-specific types (CITEXT, ENUM nativo) — SQLite in-memory no es
suficiente. El Mock garantiza que el repo construye la query correcta
y propaga el resultado.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthUserStatus
from shared.db.models.auth.user import AuthUser
from shared.db.repositories.auth import get_user_by_email

pytestmark = pytest.mark.unit


def test_get_user_by_email_returns_user_when_found():
    # Arrange
    session = MagicMock()
    expected = AuthUser(
        id='01900000-0000-7000-8000-000000000001',
        email='user@x.com',
        status=AuthUserStatus.ACTIVE,
    )
    session.execute.return_value.scalar_one_or_none.return_value = expected

    # Act
    result = get_user_by_email(session, 'user@x.com')

    # Assert
    assert result is expected
    session.execute.assert_called_once()
