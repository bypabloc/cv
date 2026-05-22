"""Integration — command 'migrate' end-to-end.

Given un evento crudo {command: 'migrate'},
When se invoca lambda_handler real,
Then el flujo handler -> controller Migrate -> run_migrate aplica el
     upgrade de Alembic y devuelve {command: 'migrate', status: 'ok'} con
     la revision aplicada.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_migrate_command_e2e(alembic_recorder):
    import handler

    # Arrange
    alembic_recorder['revision'] = '81c2cc51db34'

    # Act
    result = handler.lambda_handler(invoke_event('migrate'), lambda_context())

    # Assert
    assert result == {
        'command': 'migrate',
        'status': 'ok',
        'target': 'head',
        'current': '81c2cc51db34',
    }
    assert alembic_recorder['calls'] == [
        ('upgrade', 'head'),
        ('current', None),
    ]
