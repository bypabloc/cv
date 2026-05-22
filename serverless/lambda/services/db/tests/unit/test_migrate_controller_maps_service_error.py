"""Controller db/migrate.

Given el service run_migrate que lanza un ServiceError,
When el controller Migrate ejecuta su ciclo run(),
Then captura la excepcion y devuelve {is_valid: False} con el error_code,
     message y code del ServiceError.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_migrate_controller_maps_service_error():
    from controllers.db.migrate import Migrate
    from services.db_service import ServiceError

    # Arrange
    error = ServiceError(
        'fallo al aplicar la migracion',
        code=5000,
        error_code='DB_MIGRATE_FAILED',
    )
    with patch('controllers.db.migrate.run_migrate', side_effect=error):
        controller = Migrate(event={'target': 'head'})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'code': 5000,
        'data': {
            'error_code': 'DB_MIGRATE_FAILED',
            'message': 'fallo al aplicar la migracion',
        },
    }
