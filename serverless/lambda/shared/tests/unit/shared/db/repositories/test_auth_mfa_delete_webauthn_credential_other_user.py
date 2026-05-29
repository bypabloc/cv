"""
Given un record_id que pertenece a OTRO user,
When se llama delete_webauthn_credential (filtro WHERE user_id),
Then la query no matchea, retorna False y NO borra (anti-enumeration AC-25).
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_mfa import delete_webauthn_credential

pytestmark = pytest.mark.unit


def test_delete_webauthn_credential_returns_false_if_other_user():
    # Arrange — el filtro user_id no matchea el row de otro user.
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    ok = delete_webauthn_credential(session, user_id='u1', record_id='rec-X')

    # Assert
    assert ok is False
    session.delete.assert_not_called()
