"""Integration — command 'downgrade' sin confirm (salvaguarda).

Given un evento crudo {command: 'downgrade', args: {target: '-1'}} sin
     confirm,
When se invoca lambda_handler real,
Then el controller Downgrade rechaza la operacion destructiva, NO se
     ejecuta ningun comando de Alembic, y el handler colapsa el resultado
     a status 'error'.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_downgrade_command_without_confirm_e2e(alembic_recorder):
    import handler

    # Act
    result = handler.lambda_handler(
        invoke_event('downgrade', {'target': '-1'}), lambda_context()
    )

    # Assert
    assert result == {
        'status': 'error',
        'command': 'downgrade',
        'error': (
            "downgrade es destructivo — pasa 'confirm': true en data "
            'para ejecutarlo.'
        ),
    }
    assert alembic_recorder['calls'] == []
