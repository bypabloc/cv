"""
Given parametros validos,
When se llama insert_audit_event con event='register.start' success=True,
Then se inserta un AuthAuditLog con esos campos.
"""

from unittest.mock import MagicMock

import pytest

from shared.db.repositories.auth import insert_audit_event


pytestmark = pytest.mark.unit


def test_insert_audit_event_creates_row_with_all_fields():
    # Arrange
    session = MagicMock()

    # Act
    row = insert_audit_event(
        session,
        event='register.start',
        success=True,
        user_id='01900000-0000-7000-8000-000000000001',
        error_code=None,
        ip='203.0.113.10',
        user_agent='curl/8.0',
        niche='fintech',
        meta_data={'turnstile': 'valid'},
    )

    # Assert
    assert row.event == 'register.start'
    assert row.success is True
    assert row.user_id == '01900000-0000-7000-8000-000000000001'
    assert row.ip == '203.0.113.10'
    assert row.niche == 'fintech'
    assert row.meta_data == {'turnstile': 'valid'}
    session.add.assert_called_once_with(row)
    session.flush.assert_called_once()
