"""Handler — routing del command 'seed'.

Given un payload {command: 'seed'},
When lambda_handler lo procesa,
Then sintetiza operation='db'/action='seed', ejecuta el controller y
     devuelve el resultado del service.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import invoke_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_routes_seed_command():
    import handler

    # Arrange: se parchea la referencia que usa el controller
    # (controllers.db.seed importa run_seed con `from ... import`).
    with (
        patch(
            'controllers.db.seed.run_seed',
            return_value={'seeded': False, 'reason': 'no hay seed'},
        ),
        patch('handler.ensure_database_url'),
    ):
        # Act
        result = handler.lambda_handler(invoke_event('seed'), lambda_context())

    # Assert
    assert result == {
        'command': 'seed',
        'status': 'ok',
        'seeded': False,
        'reason': 'no hay seed',
    }
