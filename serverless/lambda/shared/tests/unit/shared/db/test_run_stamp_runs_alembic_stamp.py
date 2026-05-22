"""shared.db.migrations.run_stamp.

Given un target a marcar,
When se invoca run_stamp,
Then llama a alembic.command.stamp con ese target y devuelve la
     revision resultante.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.db.migrations import run_stamp

pytestmark = pytest.mark.unit


def test_run_stamp_runs_alembic_stamp() -> None:
    # Arrange
    with (
        patch('shared.db.migrations.command.stamp') as mock_stamp,
        patch(
            'shared.db.migrations.current_revision',
            return_value='81c2cc51db34',
        ),
    ):
        # Act
        result = run_stamp(target='head')

    # Assert
    assert mock_stamp.call_count == 1
    assert result == {'target': 'head', 'current': '81c2cc51db34'}
