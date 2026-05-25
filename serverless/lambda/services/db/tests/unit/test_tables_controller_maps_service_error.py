"""Controller db/tables — el service falla.

Given que run_tables lanza ServiceError,
When el controller Tables ejecuta su ciclo run(),
Then devuelve {is_valid: False} con el error_code y code del ServiceError.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_tables_controller_maps_service_error():
    from controllers.db.tables import Tables
    from services.db_service import ServiceError

    # Arrange
    error = ServiceError(
        'No se pudo listar las tablas: boom',
        code=5000,
        error_code='DB_QUERY_FAILED',
    )
    with patch(
        'controllers.db.tables.run_tables', side_effect=error
    ):
        controller = Tables(event={})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'code': 5000,
        'data': {
            'error_code': 'DB_QUERY_FAILED',
            'message': 'No se pudo listar las tablas: boom',
        },
    }
