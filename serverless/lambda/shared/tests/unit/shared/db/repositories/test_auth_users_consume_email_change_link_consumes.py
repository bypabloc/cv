"""
Given un magic-link email-change vigente (no consumido, no expirado),
When se llama consume_email_change_link,
Then setea consumed_at, hace flush y retorna el link.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import consume_email_change_link

pytestmark = pytest.mark.unit


def test_consume_email_change_link_marks_consumed():
    # Arrange
    session = MagicMock()
    link = MagicMock()
    link.consumed_at = None
    link.expires_at = datetime(2099, 1, 1, 0, 0, 0, tzinfo=UTC)
    session.execute.return_value.scalar_one_or_none.return_value = link

    # Act
    result = consume_email_change_link(session, token_hash=b'h' * 32)

    # Assert
    assert result is link
    assert link.consumed_at is not None
    session.flush.assert_called_once()
