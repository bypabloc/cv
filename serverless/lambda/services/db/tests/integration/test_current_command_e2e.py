"""Integration — command 'current' end-to-end.

Given un evento crudo {command: 'current'},
When se invoca lambda_handler real,
Then el flujo handler -> controller Current -> run_current consulta la
     revision aplicada y devuelve {command: 'current', status: 'ok'}.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_current_command_e2e(alembic_recorder):
    import handler

    # Arrange
    alembic_recorder['revision'] = '81c2cc51db34'

    # Act
    result = handler.lambda_handler(invoke_event('current'), lambda_context())

    # Assert
    assert result == {
        'command': 'current',
        'status': 'ok',
        'current': '81c2cc51db34',
    }
    assert alembic_recorder['calls'] == [('current', None)]
