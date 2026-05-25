"""shared.db.migrations.run_downgrade.

Given un target de downgrade,
When se invoca run_downgrade,
Then llama a alembic.command.downgrade con ese target y devuelve la
     revision resultante.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.db.migrations import run_downgrade

pytestmark = pytest.mark.unit


def test_run_downgrade_runs_alembic_downgrade() -> None:
    # Arrange
    with (
        patch('shared.db.migrations.command.downgrade') as mock_downgrade,
        patch(
            'shared.db.migrations.current_revision',
            return_value='base',
        ),
    ):
        # Act
        result = run_downgrade(target='-1')

    # Assert
    assert mock_downgrade.call_count == 1
    assert result == {'target': '-1', 'current': 'base'}
