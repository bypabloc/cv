"""
Given los datos de un cambio de consentimiento,
When se llama insert_consent_log,
Then hace session.add + flush y retorna el row agregado.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import insert_consent_log

pytestmark = pytest.mark.unit


def test_insert_consent_log_adds_and_returns_row():
    # Arrange
    session = MagicMock()

    # Act
    row = insert_consent_log(
        session,
        user_id='u1',
        field='marketing_consent',
        old_value='false',
        new_value='true',
    )

    # Assert
    assert row.field == 'marketing_consent'
    session.add.assert_called_once_with(row)
    session.flush.assert_called_once()
