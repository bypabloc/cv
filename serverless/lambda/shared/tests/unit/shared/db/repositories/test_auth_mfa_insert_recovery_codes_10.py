"""
Given 10 hashes de recovery codes,
When se llama insert_recovery_codes,
Then se hace session.add 10 veces y un flush.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_mfa import insert_recovery_codes

pytestmark = pytest.mark.unit


def test_insert_recovery_codes_adds_ten_rows():
    # Arrange
    session = MagicMock()
    hashes = [bytes([i]) * 32 for i in range(10)]

    # Act
    insert_recovery_codes(session, user_id='u1', code_hashes=hashes)

    # Assert
    assert session.add.call_count == 10
    session.flush.assert_called_once()
