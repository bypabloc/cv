"""Integration — command 'migrate' con un target explicito.

Given un evento crudo {command: 'migrate', args: {target: '<rev>'}},
When se invoca lambda_handler real,
Then el upgrade de Alembic se ejecuta hacia esa revision y el resultado
     refleja el target pedido.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_migrate_command_with_target_e2e(alembic_recorder):
    import handler

    # Arrange
    alembic_recorder['revision'] = 'abc123def456'

    # Act
    result = handler.lambda_handler(
        invoke_event('migrate', {'target': 'abc123def456'}),
        lambda_context(),
    )

    # Assert
    assert result == {
        'command': 'migrate',
        'status': 'ok',
        'target': 'abc123def456',
        'current': 'abc123def456',
    }
    assert alembic_recorder['calls'] == [
        ('upgrade', 'abc123def456'),
        ('current', None),
    ]
