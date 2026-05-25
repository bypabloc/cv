"""Controller db/stamp.

Given el service run_stamp que lanza un ServiceError,
When el controller Stamp ejecuta su ciclo run(),
Then captura la excepcion y devuelve {is_valid: False} con el error_code,
     message y code del ServiceError.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_stamp_controller_maps_service_error():
    from controllers.db.stamp import Stamp
    from services.db_service import ServiceError

    # Arrange
    error = ServiceError(
        'fallo al marcar la revision',
        code=5000,
        error_code='DB_STAMP_FAILED',
    )
    with patch('controllers.db.stamp.run_stamp', side_effect=error):
        controller = Stamp(event={'target': 'head'})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'code': 5000,
        'data': {
            'error_code': 'DB_STAMP_FAILED',
            'message': 'fallo al marcar la revision',
        },
    }
