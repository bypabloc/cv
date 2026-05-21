"""Service db_service.run_downgrade.

Given un target de downgrade,
When se invoca run_downgrade,
Then llama a alembic.command.downgrade con ese target y devuelve la
     revision resultante.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_downgrade_service_runs_alembic_downgrade():
    from services.db_service import run_downgrade

    # Arrange
    with (
        patch('services.db_service.command.downgrade') as mock_downgrade,
        patch(
            'services.db_service.current_revision',
            return_value='rev1',
        ),
    ):
        # Act
        result = run_downgrade(target='-1')

    # Assert
    assert mock_downgrade.call_count == 1
    assert result == {'target': '-1', 'current': 'rev1'}
