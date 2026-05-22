"""Service db_service.run_tables.

Given que shared.db.repository.list_tables lanza un RepositoryError,
When se invoca run_tables,
Then lo traduce a un ServiceError con el mismo code y error_code.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_tables_service_translates_repository_error():
    from services.db_service import ServiceError, run_tables
    from shared.db.repository import RepositoryError

    # Arrange
    error = RepositoryError(
        'No se pudo listar las tablas: timeout',
        code=5000,
        error_code='DB_QUERY_FAILED',
    )
    with (
        patch(
            'services.db_service._shared_list_tables',
            side_effect=error,
        ),
        pytest.raises(ServiceError) as exc_info,
    ):
        # Act
        run_tables()

    # Assert
    assert exc_info.value.code == 5000
    assert exc_info.value.error_code == 'DB_QUERY_FAILED'
    assert exc_info.value.message == 'No se pudo listar las tablas: timeout'
