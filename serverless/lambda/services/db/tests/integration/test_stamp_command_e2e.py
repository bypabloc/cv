"""Integration — command 'stamp' end-to-end.

Given un evento crudo {command: 'stamp', args: {target: 'head'}},
When se invoca lambda_handler real,
Then el flujo handler -> controller Stamp -> run_stamp marca la revision
     en Alembic sin ejecutar SQL y devuelve {command: 'stamp',
     status: 'ok'}.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_stamp_command_e2e(alembic_recorder):
    import handler

    # Arrange
    alembic_recorder['revision'] = '81c2cc51db34'

    # Act
    result = handler.lambda_handler(
        invoke_event('stamp', {'target': 'head'}), lambda_context()
    )

    # Assert
    assert result == {
        'command': 'stamp',
        'status': 'ok',
        'target': 'head',
        'current': '81c2cc51db34',
    }
    assert alembic_recorder['calls'] == [
        ('stamp', 'head'),
        ('current', None),
    ]
