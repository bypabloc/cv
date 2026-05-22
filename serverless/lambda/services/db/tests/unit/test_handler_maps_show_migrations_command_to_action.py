"""Handler — el command 'show-migrations' (guion) mapea a la action
'show_migrations' (underscore).

Given un payload {command: 'show-migrations'},
When lambda_handler lo procesa,
Then resuelve el controller Show_migrations y devuelve su resultado.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import invoke_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_maps_show_migrations_command_to_action():
    import handler

    # Arrange
    with (
        patch(
            'services.db_service.run_show_migrations',
            return_value={'history': ['rev1 (head)'], 'current': 'rev1'},
        ),
        patch('handler.ensure_database_url'),
    ):
        # Act
        result = handler.lambda_handler(
            invoke_event('show-migrations'), lambda_context()
        )

    # Assert
    assert result == {
        'command': 'show-migrations',
        'status': 'ok',
        'history': ['rev1 (head)'],
        'current': 'rev1',
    }
