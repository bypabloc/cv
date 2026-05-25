"""Handler — routing del command 'current'.

Given un payload {command: 'current'},
When lambda_handler lo procesa,
Then sintetiza operation='db'/action='current', ejecuta el controller y
     devuelve el resultado del service.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import invoke_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_routes_current_command():
    import handler

    # Arrange: se parchea la referencia que usa el controller
    # (controllers.db.current importa run_current con `from ... import`).
    with (
        patch(
            'controllers.db.current.run_current',
            return_value={'current': '81c2cc51db34'},
        ),
        patch('handler.ensure_database_url'),
    ):
        # Act
        result = handler.lambda_handler(
            invoke_event('current'), lambda_context()
        )

    # Assert
    assert result == {
        'command': 'current',
        'status': 'ok',
        'current': '81c2cc51db34',
    }
