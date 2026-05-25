"""Controller db/downgrade.

Given un payload con confirm: true y el service run_downgrade que lanza
     un ServiceError,
When el controller Downgrade ejecuta su ciclo run(),
Then captura la excepcion y devuelve {is_valid: False} con el error_code,
     message y code del ServiceError.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_downgrade_controller_maps_service_error():
    from controllers.db.downgrade import Downgrade
    from services.db_service import ServiceError

    # Arrange
    error = ServiceError(
        'fallo al revertir la migracion',
        code=5000,
        error_code='DB_DOWNGRADE_FAILED',
    )
    with patch('controllers.db.downgrade.run_downgrade', side_effect=error):
        controller = Downgrade(event={'target': '-1', 'confirm': True})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'code': 5000,
        'data': {
            'error_code': 'DB_DOWNGRADE_FAILED',
            'message': 'fallo al revertir la migracion',
        },
    }
