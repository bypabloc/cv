"""Controller db/show_migrations.

Given el service run_show_migrations que lanza un ServiceError,
When el controller ShowMigrations ejecuta su ciclo run(),
Then captura la excepcion y devuelve {is_valid: False} con el error_code,
     message y code del ServiceError.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_show_migrations_controller_maps_service_error():
    from controllers.db.show_migrations import ShowMigrations
    from services.db_service import ServiceError

    # Arrange
    error = ServiceError(
        'fallo al leer el historial',
        code=5000,
        error_code='DB_HISTORY_FAILED',
    )
    with patch(
        'controllers.db.show_migrations.run_show_migrations',
        side_effect=error,
    ):
        controller = ShowMigrations(event={})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'code': 5000,
        'data': {
            'error_code': 'DB_HISTORY_FAILED',
            'message': 'fallo al leer el historial',
        },
    }
