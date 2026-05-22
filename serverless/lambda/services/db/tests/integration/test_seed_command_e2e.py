"""Integration — command 'seed' end-to-end.

Given un evento crudo {command: 'seed'},
When se invoca lambda_handler real,
Then el flujo handler -> controller Seed -> run_seed reporta honestamente
     que no hay seed disponible para el schema unificado y devuelve
     {command: 'seed', status: 'ok', seeded: False}.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_seed_command_e2e():
    import handler

    # Act
    result = handler.lambda_handler(invoke_event('seed'), lambda_context())

    # Assert
    assert result == {
        'command': 'seed',
        'status': 'ok',
        'seeded': False,
        'reason': (
            'no hay seed disponible para el schema unificado de '
            'shared/db/ — el seed legacy de db/cv/ no esta migrado'
        ),
    }
