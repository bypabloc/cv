"""Handler — routing del command 'tables'.

Given un payload {command: 'tables'},
When lambda_handler lo procesa,
Then sintetiza operation='db'/action='tables', ejecuta el controller y
     devuelve el resultado del service.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import invoke_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_routes_tables_command():
    import handler

    # Arrange
    with (
        patch(
            'services.db_service.run_tables',
            return_value={
                'tables': [{'name': 'public.contacts', 'rows': 200}],
            },
        ),
        patch('handler.ensure_database_url'),
    ):
        # Act
        result = handler.lambda_handler(
            invoke_event('tables'), lambda_context()
        )

    # Assert
    assert result == {
        'command': 'tables',
        'status': 'ok',
        'tables': [{'name': 'public.contacts', 'rows': 200}],
    }
