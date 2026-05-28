"""Integration — command 'show-migrations' end-to-end.

Given un evento crudo {command: 'show-migrations'} (con guion),
When se invoca lambda_handler real,
Then el handler mapea el command 'show-migrations' a la action
     'show_migrations', el flujo controller ShowMigrations ->
     run_show_migrations consulta el historial de Alembic y devuelve
     {command: 'show-migrations', status: 'ok'} con la lista de lineas.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_show_migrations_command_e2e(alembic_recorder):
    import handler

    # Arrange
    alembic_recorder['history'] = 'rev0 -> rev1\nrev1 -> rev2 (head)'
    alembic_recorder['revision'] = 'rev2'

    # Act
    result = handler.lambda_handler(
        invoke_event('show-migrations'), lambda_context()
    )

    # Assert
    assert result == {
        'command': 'show-migrations',
        'status': 'ok',
        'history': ['rev0 -> rev1', 'rev1 -> rev2 (head)'],
        'current': 'rev2',
    }
    assert alembic_recorder['calls'] == [
        ('history', None),
        ('current', None),
    ]
