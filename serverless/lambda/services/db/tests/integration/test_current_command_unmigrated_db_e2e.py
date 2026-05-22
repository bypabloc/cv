"""Integration — command 'current' contra una DB sin migrar.

Given un evento crudo {command: 'current'} y una DB sin ninguna revision
     aplicada (Alembic no imprime nada),
When se invoca lambda_handler real,
Then el resultado reporta current None.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_current_command_unmigrated_db_e2e(alembic_recorder):
    import handler

    # Arrange: DB sin migrar -> command.current no escribe nada.
    alembic_recorder['revision'] = ''

    # Act
    result = handler.lambda_handler(invoke_event('current'), lambda_context())

    # Assert
    assert result == {
        'command': 'current',
        'status': 'ok',
        'current': None,
    }
