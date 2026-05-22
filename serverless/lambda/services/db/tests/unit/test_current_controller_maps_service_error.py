"""Controller db/current.

Given el service run_current que lanza un ServiceError,
When el controller Current ejecuta su ciclo run(),
Then captura la excepcion y devuelve {is_valid: False} con el error_code,
     message y code del ServiceError.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_current_controller_maps_service_error():
    from controllers.db.current import Current
    from services.db_service import ServiceError

    # Arrange
    error = ServiceError(
        'fallo al leer la revision actual',
        code=5000,
        error_code='DB_CURRENT_FAILED',
    )
    with patch('controllers.db.current.run_current', side_effect=error):
        controller = Current(event={})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'code': 5000,
        'data': {
            'error_code': 'DB_CURRENT_FAILED',
            'message': 'fallo al leer la revision actual',
        },
    }
