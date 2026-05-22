"""Handler — payload sin 'command'.

Given un payload vacio (sin 'command'),
When lambda_handler lo procesa,
Then devuelve status 'error' con la lista de commands disponibles.
"""

import pytest

from tests.unit._helpers import lambda_context

pytestmark = pytest.mark.unit


def test_handler_rejects_missing_command():
    import handler

    # Act
    result = handler.lambda_handler({}, lambda_context())

    # Assert
    assert result['status'] == 'error'
    assert result['available'] == [
        'current',
        'downgrade',
        'migrate',
        'seed',
        'show-migrations',
        'stamp',
        'tables',
    ]
