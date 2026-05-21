"""Service db_service.run_migrate.

Given un target de migracion,
When se invoca run_migrate,
Then llama a alembic.command.upgrade con ese target y devuelve la
     revision resultante.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_migrate_service_runs_alembic_upgrade():
    from services.db_service import run_migrate

    # Arrange
    with (
        patch('services.db_service.command.upgrade') as mock_upgrade,
        patch(
            'services.db_service.current_revision',
            return_value='81c2cc51db34',
        ),
    ):
        # Act
        result = run_migrate(target='head')

    # Assert
    assert mock_upgrade.call_count == 1
    assert result == {'target': 'head', 'current': '81c2cc51db34'}
