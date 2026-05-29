"""
Given un AuthUser pending,
When se llama mark_user_active,
Then status=active, email_verified_at se setea, failed_attempts=0.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from shared.db.models.auth import AuthUser, AuthUserStatus
from shared.db.repositories.auth import mark_user_active

pytestmark = pytest.mark.unit


def test_mark_user_active_updates_status_and_resets_attempts():
    # Arrange
    session = MagicMock()
    user = AuthUser(
        id='01900000-0000-7000-8000-000000000001',
        email='u@x.com',
        status=AuthUserStatus.PENDING,
        failed_attempts=3,
    )
    user.created_at = datetime.now(UTC)
    when = datetime(2026, 5, 28, 12, 0, 0, tzinfo=UTC)

    # Act
    mark_user_active(session, user, when=when)

    # Assert
    assert user.status == AuthUserStatus.ACTIVE
    assert user.email_verified_at == when
    assert user.failed_attempts == 0
    session.flush.assert_called_once()
