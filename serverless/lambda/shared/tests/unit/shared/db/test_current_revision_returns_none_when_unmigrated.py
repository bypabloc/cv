"""shared.db.migrations.current_revision.

Given una DB sin migrar (Alembic no imprime ninguna revision),
When se invoca current_revision,
Then devuelve None.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.db.migrations import current_revision

pytestmark = pytest.mark.unit


def test_current_revision_returns_none_when_unmigrated() -> None:
    # Arrange + Act
    with patch('shared.db.migrations._capture', return_value=''):
        result = current_revision()

    # Assert
    assert result is None
