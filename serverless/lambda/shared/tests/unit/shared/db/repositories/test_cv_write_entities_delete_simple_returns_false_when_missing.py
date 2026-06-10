"""shared.db.repositories.cv_write_entities.delete_simple.

Given un slug que NO existe en cv_certificates,
When se invoca delete_simple('certificate', slug),
Then devuelve False y NO ejecuta ningun delete (solo el select de lookup).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.cv_write_entities import delete_simple

pytestmark = pytest.mark.unit


def test_cv_write_entities_delete_simple_returns_false_when_missing() -> None:
    # Arrange
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    # Act
    deleted = delete_simple(session, 'certificate', 'no-existe')

    # Assert: solo el SELECT de lookup, ningun DELETE
    assert deleted is False
    assert session.execute.call_count == 1
