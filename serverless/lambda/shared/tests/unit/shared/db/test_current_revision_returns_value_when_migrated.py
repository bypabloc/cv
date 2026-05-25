"""shared.db.migrations.current_revision.

Given una DB migrada (Alembic imprime la revision aplicada),
When se invoca current_revision,
Then devuelve esa revision.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.db.migrations import current_revision

pytestmark = pytest.mark.unit


def test_current_revision_returns_value_when_migrated() -> None:
    # Arrange + Act
    with patch(
        'shared.db.migrations._capture', return_value='81c2cc51db34'
    ):
        result = current_revision()

    # Assert
    assert result == '81c2cc51db34'
