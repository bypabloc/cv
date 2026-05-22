"""Service db_service.run_show_migrations.

Given un historial de migraciones,
When se invoca run_show_migrations,
Then devuelve el historial como lista de lineas y la revision actual.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_show_migrations_service_returns_history():
    from services.db_service import run_show_migrations

    # Arrange
    with (
        patch(
            'services.db_service._capture',
            return_value='rev1 -> rev2 (head)',
        ),
        patch(
            'services.db_service.current_revision',
            return_value='rev2',
        ),
    ):
        # Act
        result = run_show_migrations()

    # Assert
    assert result == {
        'history': ['rev1 -> rev2 (head)'],
        'current': 'rev2',
    }
