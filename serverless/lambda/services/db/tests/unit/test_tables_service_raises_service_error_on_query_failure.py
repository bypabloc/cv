"""Service db_service.run_tables — fallo de la query.

Given que la query a pg_stat_user_tables falla,
When se invoca run_tables,
Then lanza ServiceError con code=5000 y error_code='DB_QUERY_FAILED'.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_tables_service_raises_service_error_on_query_failure():
    from services.db_service import ServiceError, run_tables

    # Arrange
    with (
        patch.dict(os.environ, {'DATABASE_URL': 'postgresql://x/y'}),
        patch(
            'sqlalchemy.create_engine',
            side_effect=RuntimeError('connection refused'),
        ),
        pytest.raises(ServiceError) as exc_info,
    ):
        # Act
        run_tables()

    # Assert
    assert exc_info.value.code == 5000
    assert exc_info.value.error_code == 'DB_QUERY_FAILED'
