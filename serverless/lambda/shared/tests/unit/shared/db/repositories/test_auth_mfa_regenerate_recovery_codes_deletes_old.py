"""
Given un user con recovery codes viejos,
When se llama regenerate_recovery_codes con 10 hashes nuevos,
Then ejecuta un DELETE de los viejos y hace add de los 10 nuevos.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_mfa import regenerate_recovery_codes

pytestmark = pytest.mark.unit


def test_regenerate_recovery_codes_deletes_old_and_inserts_new():
    # Arrange
    session = MagicMock()
    hashes = [bytes([i]) * 32 for i in range(10)]

    # Act
    regenerate_recovery_codes(session, user_id='u1', code_hashes=hashes)

    # Assert — un execute (el DELETE) + 10 add (los INSERT).
    session.execute.assert_called_once()
    assert session.add.call_count == 10
