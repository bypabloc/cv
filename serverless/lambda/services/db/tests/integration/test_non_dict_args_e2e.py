"""Integration — invocacion con 'args' que no es un objeto.

Given un evento crudo {command: 'migrate', args: <no-objeto>},
When se invoca lambda_handler real,
Then devuelve status 'error' indicando que 'args' debe ser un objeto.
"""

import pytest

from tests.integration._fixtures._invocation import lambda_context

pytestmark = pytest.mark.integration


def test_non_dict_args_e2e():
    import handler

    # Act
    result = handler.lambda_handler(
        {'command': 'migrate', 'args': ['not', 'an', 'object']},
        lambda_context(),
    )

    # Assert
    assert result == {
        'status': 'error',
        'error': "'args' debe ser un objeto.",
    }
