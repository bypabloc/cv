"""shared.db.migrations.run_show_migrations.

Given el historial de migraciones de Alembic,
When se invoca run_show_migrations,
Then devuelve la lista de lineas del historial y la revision actual.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.db.migrations import run_show_migrations

pytestmark = pytest.mark.unit


def test_run_show_migrations_returns_history() -> None:
    # Arrange
    with (
        patch(
            'shared.db.migrations._capture',
            return_value='rev1 -> rev2\nrev2 -> rev3 (head)',
        ),
        patch(
            'shared.db.migrations.current_revision',
            return_value='rev3',
        ),
    ):
        # Act
        result = run_show_migrations()

    # Assert
    assert result == {
        'history': ['rev1 -> rev2', 'rev2 -> rev3 (head)'],
        'current': 'rev3',
    }
