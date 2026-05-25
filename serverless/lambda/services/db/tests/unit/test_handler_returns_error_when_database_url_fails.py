"""Handler — ensure_database_url falla.

Given un payload {command: 'current'} y ensure_database_url que lanza,
When lambda_handler lo procesa,
Then devuelve status 'error' indicando que no se pudo resolver
     DATABASE_URL, sin ejecutar el controller.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import invoke_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_returns_error_when_database_url_fails():
    import handler

    # Arrange
    with patch(
        'handler.ensure_database_url',
        side_effect=RuntimeError('SSM parameter not found'),
    ):
        # Act
        result = handler.lambda_handler(
            invoke_event('current'), lambda_context()
        )

    # Assert
    assert result == {
        'status': 'error',
        'command': 'current',
        'error': 'No se pudo resolver DATABASE_URL — ver CloudWatch.',
    }
