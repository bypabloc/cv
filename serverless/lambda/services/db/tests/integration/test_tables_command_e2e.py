"""Integration — command 'tables' end-to-end.

Given un evento crudo {command: 'tables'} y una DB con tablas de usuario,
When se invoca lambda_handler real,
Then el flujo handler -> controller Tables -> run_tables consulta
     pg_stat_user_tables y devuelve {command: 'tables', status: 'ok'} con
     cada tabla y su estimado de filas.
"""

from unittest.mock import patch

import pytest

from tests.integration._fixtures._engine import fake_engine_with_rows
from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_tables_command_e2e():
    import handler

    # Arrange: engine SQLAlchemy falso (la DB es la unica frontera de E/S).
    engine = fake_engine_with_rows(
        [('public.tracking_events', 15000), ('public.contacts', 200)]
    )

    # Act
    with patch('sqlalchemy.create_engine', return_value=engine):
        result = handler.lambda_handler(
            invoke_event('tables'), lambda_context()
        )

    # Assert
    assert result == {
        'command': 'tables',
        'status': 'ok',
        'tables': [
            {'name': 'public.tracking_events', 'rows': 15000},
            {'name': 'public.contacts', 'rows': 200},
        ],
    }
