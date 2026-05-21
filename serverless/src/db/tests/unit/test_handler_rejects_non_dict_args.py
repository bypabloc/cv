"""Handler — 'args' con tipo invalido.

Given un payload {command: 'migrate', args: 'no-soy-objeto'},
When lambda_handler lo procesa,
Then devuelve status 'error' indicando que 'args' debe ser un objeto.
"""

import pytest

from tests.unit._helpers import lambda_context

pytestmark = pytest.mark.unit


def test_handler_rejects_non_dict_args():
    import handler

    # Act
    result = handler.lambda_handler(
        {'command': 'migrate', 'args': 'no-soy-objeto'},
        lambda_context(),
    )

    # Assert
    assert result['status'] == 'error'
    assert result['error'] == "'args' debe ser un objeto."
