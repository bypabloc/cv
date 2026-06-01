"""
Given un magic-link email-change ya expirado,
When se llama consume_email_change_link (expires_at en el pasado),
Then retorna None sin hacer flush.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import consume_email_change_link

pytestmark = pytest.mark.unit


def test_consume_email_change_link_returns_none_when_expired():
    # Arrange
    session = MagicMock()
    link = MagicMock()
    link.consumed_at = None
    link.expires_at = datetime(2000, 1, 1, 0, 0, 0, tzinfo=UTC)
    session.execute.return_value.scalar_one_or_none.return_value = link

    # Act
    result = consume_email_change_link(session, token_hash=b'h' * 32)

    # Assert
    assert result is None
    session.flush.assert_not_called()
