"""shared.db.migrations.run_migrate.

Given un target de migracion,
When se invoca run_migrate,
Then llama a alembic.command.upgrade con ese target y devuelve la
     revision resultante.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.db.migrations import run_migrate

pytestmark = pytest.mark.unit


def test_run_migrate_runs_alembic_upgrade() -> None:
    # Arrange
    with (
        patch('shared.db.migrations.command.upgrade') as mock_upgrade,
        patch(
            'shared.db.migrations.current_revision',
            return_value='81c2cc51db34',
        ),
    ):
        # Act
        result = run_migrate(target='head')

    # Assert
    assert mock_upgrade.call_count == 1
    assert result == {'target': 'head', 'current': '81c2cc51db34'}
