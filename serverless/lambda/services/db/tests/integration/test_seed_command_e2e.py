"""Integration — command 'seed' end-to-end.

Given un evento crudo {command: 'seed'} y la DB con el schema migrado,
When se invoca lambda_handler real,
Then el flujo handler -> controller Seed -> run_seed lee los YAML de
     seeds/data/, los inserta en la DB y devuelve {status: 'ok',
     seeded: True} con los conteos por tabla.
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
    assert result['command'] == 'seed'
    assert result['status'] == 'ok'
    assert result['seeded'] is True
    counts = result['counts']
    # El seed real puebla las tablas del CV con la data de los YAML.
    assert counts['profile'] == 1
    assert counts['niches'] == 5
    assert counts['experiences'] == 9
    assert counts['projects'] == 6
    assert counts['skill_categories'] == 10
    assert counts['certificates'] == 11
    assert counts['references'] == 10


def test_seed_command_is_idempotent_e2e():
    """Given el seed ya aplicado,
    When se invoca el command 'seed' una segunda vez,
    Then los conteos por tabla son identicos (upsert idempotente).
    """
    import handler

    # Act
    first = handler.lambda_handler(invoke_event('seed'), lambda_context())
    second = handler.lambda_handler(invoke_event('seed'), lambda_context())

    # Assert
    assert first['counts'] == second['counts']
