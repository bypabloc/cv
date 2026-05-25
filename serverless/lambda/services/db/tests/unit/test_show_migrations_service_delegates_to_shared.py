"""Service db_service.run_show_migrations.

Given el historial de migraciones,
When se invoca run_show_migrations,
Then delega en shared.db.migrations.run_show_migrations.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_show_migrations_service_delegates_to_shared():
    from services.db_service import run_show_migrations

    # Arrange
    expected = {'history': ['rev1 -> rev2'], 'current': 'rev2'}
    with patch(
        'services.db_service._shared_run_show_migrations',
        return_value=expected,
    ) as mock_shared:
        # Act
        result = run_show_migrations()

    # Assert
    assert result == expected
    assert mock_shared.call_count == 1
