"""Controller db/seed.

Given el service run_seed que lanza un ServiceError,
When el controller Seed ejecuta su ciclo run(),
Then captura la excepcion y devuelve {is_valid: False} con el error_code,
     message y code del ServiceError.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_seed_controller_maps_service_error():
    from controllers.db.seed import Seed
    from services.db_service import ServiceError

    # Arrange
    error = ServiceError(
        'fallo al cargar el seed',
        code=5000,
        error_code='DB_SEED_FAILED',
    )
    with patch('controllers.db.seed.run_seed', side_effect=error):
        controller = Seed(event={})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'code': 5000,
        'data': {
            'error_code': 'DB_SEED_FAILED',
            'message': 'fallo al cargar el seed',
        },
    }
