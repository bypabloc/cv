"""Test: AuthEmailMessage acepta los kinds nuevos del plan 03.

Given un payload con kind 'account-disabled' y campos validos,
When se construye AuthEmailMessage,
Then valida sin error y msg.kind es 'account-disabled'.

Plan 03 (gestion de usuarios): AuthEmailKind se extendio con los 4
kinds nuevos (email-change-verify, email-changed, account-disabled,
account-deleted).
"""

import pytest

pytestmark = pytest.mark.unit


def test_message_accepts_new_kinds():
    """AuthEmailMessage valida el kind nuevo 'account-disabled'."""
    from models.message import AuthEmailMessage

    # Arrange / Act
    msg = AuthEmailMessage(
        kind='account-disabled',
        to='u@x.com',
        user_id='01900000-0000-7000-8000-000000000001',
        subject_id='s',
        data={'reason': 'x'},
    )

    # Assert
    assert msg.kind == 'account-disabled'
