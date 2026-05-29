"""
Given un user con un row TOTP previo,
When se llama upsert_totp_method (re-setup),
Then reusa el row: reescribe el ciphertext y resetea confirmed_at/disabled_at.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from shared.db.models.auth import AuthMfaKind, AuthMfaMethod
from shared.db.repositories.auth_mfa import upsert_totp_method

pytestmark = pytest.mark.unit


def test_upsert_totp_method_reuses_existing_row():
    # Arrange — ya existe un row TOTP confirmado.
    session = MagicMock()
    existing = AuthMfaMethod(
        user_id='u1',
        kind=AuthMfaKind.TOTP,
        totp_secret_ciphertext=b'old-ct',
        confirmed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    session.execute.return_value.scalar_one_or_none.return_value = existing

    # Act
    method = upsert_totp_method(session, user_id='u1', ciphertext=b'new-ct')

    # Assert
    assert method is existing
    assert method.totp_secret_ciphertext == b'new-ct'
    assert method.confirmed_at is None
    assert method.disabled_at is None
    session.add.assert_not_called()
    session.flush.assert_called_once()
