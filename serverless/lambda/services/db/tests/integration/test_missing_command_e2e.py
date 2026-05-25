"""Integration — invocacion sin 'command'.

Given un evento crudo sin la clave 'command',
When se invoca lambda_handler real,
Then devuelve status 'error' y la lista de commands disponibles, sin
     resolver ningun controller.
"""

import pytest

from tests.integration._fixtures._invocation import lambda_context

pytestmark = pytest.mark.integration


def test_missing_command_e2e():
    import handler

    # Act
    result = handler.lambda_handler({}, lambda_context())

    # Assert
    assert result['status'] == 'error'
    assert result['error'] == "Falta 'command' en el payload."
    assert result['available'] == [
        'current',
        'downgrade',
        'migrate',
        'seed',
        'show-migrations',
        'stamp',
        'tables',
    ]
