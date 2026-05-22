"""Integration — command 'tables' contra una DB inaccesible.

Given un evento crudo {command: 'tables'} y un engine cuya conexion falla,
When se invoca lambda_handler real,
Then run_tables lanza un ServiceError, el controller Tables lo normaliza a
     {is_valid: False} y el handler lo colapsa a status 'error'.
"""

from unittest.mock import patch

import pytest

from tests.integration._fixtures._engine import failing_engine
from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_tables_command_query_failure_e2e():
    import handler

    # Arrange: la conexion del engine falla al usarse.
    engine = failing_engine('connection refused')

    # Act
    with patch('sqlalchemy.create_engine', return_value=engine):
        result = handler.lambda_handler(
            invoke_event('tables'), lambda_context()
        )

    # Assert
    assert result['status'] == 'error'
    assert result['command'] == 'tables'
    assert 'No se pudo listar las tablas' in result['error']
