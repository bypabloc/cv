"""Integration — invocacion con un command desconocido.

Given un evento crudo {command: 'bogus'} cuyo controller no existe,
When se invoca lambda_handler real,
Then el flujo validate_event -> import_controller no resuelve un
     controller y el handler devuelve status 'error' con la lista de
     commands disponibles.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_unknown_command_e2e():
    import handler

    # Act
    result = handler.lambda_handler(invoke_event('bogus'), lambda_context())

    # Assert
    assert result['status'] == 'error'
    assert result['error'] == "command desconocido: 'bogus'."
    assert result['available'] == [
        'current',
        'downgrade',
        'migrate',
        'seed',
        'show-migrations',
        'stamp',
        'tables',
    ]
