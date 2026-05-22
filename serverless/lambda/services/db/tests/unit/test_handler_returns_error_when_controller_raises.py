"""Handler — el controller lanza una excepcion generica.

Given un payload {command: 'current'} y el service run_current que lanza
     una excepcion no controlada (no ServiceError),
When lambda_handler lo procesa,
Then captura la excepcion y devuelve status 'error' indicando que el
     command fallo.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import invoke_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_returns_error_when_controller_raises():
    import handler

    # Arrange: se parchea la referencia que usa el controller
    # (controllers.db.current importa run_current con `from ... import`).
    with (
        patch('handler.ensure_database_url'),
        patch(
            'controllers.db.current.run_current',
            side_effect=RuntimeError('conexion perdida'),
        ),
    ):
        # Act
        result = handler.lambda_handler(
            invoke_event('current'), lambda_context()
        )

    # Assert
    assert result == {
        'status': 'error',
        'command': 'current',
        'error': 'El command fallo — ver los logs de CloudWatch.',
    }
