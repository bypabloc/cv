"""Integration — command 'downgrade' con confirm: true.

Given un evento crudo {command: 'downgrade', args: {target: '-1',
     confirm: true}},
When se invoca lambda_handler real,
Then el flujo handler -> controller Downgrade -> run_downgrade ejecuta el
     downgrade de Alembic y devuelve {command: 'downgrade', status: 'ok'}.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_downgrade_command_confirmed_e2e(alembic_recorder):
    import handler

    # Arrange
    alembic_recorder['revision'] = 'rev_previous'

    # Act
    result = handler.lambda_handler(
        invoke_event('downgrade', {'target': '-1', 'confirm': True}),
        lambda_context(),
    )

    # Assert
    assert result == {
        'command': 'downgrade',
        'status': 'ok',
        'target': '-1',
        'current': 'rev_previous',
    }
    assert alembic_recorder['calls'] == [
        ('downgrade', '-1'),
        ('current', None),
    ]
