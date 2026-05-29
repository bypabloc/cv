"""
Given que no hay recovery code activo que matchee (ya consumido o inexistente),
When se llama consume_recovery_code,
Then retorna False y NO hace flush.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_mfa import consume_recovery_code

pytestmark = pytest.mark.unit


def test_consume_recovery_code_returns_false_when_no_active_row():
    # Arrange — el filtro consumed_at IS NULL no matchea ninguna fila.
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    ok = consume_recovery_code(session, user_id='u1', code_hash=b'h' * 32)

    # Assert
    assert ok is False
    session.flush.assert_not_called()
