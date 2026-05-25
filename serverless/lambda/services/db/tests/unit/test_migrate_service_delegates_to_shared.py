"""Service db_service.run_migrate.

Given un target de migracion,
When se invoca run_migrate,
Then delega en shared.db.migrations.run_migrate con ese target y
     devuelve su resultado tal cual.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_migrate_service_delegates_to_shared():
    from services.db_service import run_migrate

    # Arrange
    expected = {'target': 'head', 'current': 'rev1'}
    with patch(
        'services.db_service._shared_run_migrate',
        return_value=expected,
    ) as mock_shared:
        # Act
        result = run_migrate(target='head')

    # Assert
    assert result == expected
    assert mock_shared.call_count == 1
    assert mock_shared.call_args.kwargs == {'target': 'head'}
