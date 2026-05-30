"""
Given un recovery code activo que matchea,
When se llama consume_recovery_code,
Then setea consumed_at != None y retorna True.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.recovery_code import AuthMfaRecoveryCode
from shared.db.repositories.auth_mfa import consume_recovery_code

pytestmark = pytest.mark.unit


def test_consume_recovery_code_marks_consumed():
    # Arrange
    session = MagicMock()
    row = AuthMfaRecoveryCode(user_id='u1', code_hash=b'h' * 32)
    session.execute.return_value.scalar_one_or_none.return_value = row

    # Act
    ok = consume_recovery_code(session, user_id='u1', code_hash=b'h' * 32)

    # Assert
    assert ok is True
    assert row.consumed_at is not None
    session.flush.assert_called_once()
