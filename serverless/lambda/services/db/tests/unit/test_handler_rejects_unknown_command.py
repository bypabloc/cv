"""Handler — command desconocido.

Given un payload {command: 'bogus'},
When lambda_handler lo procesa,
Then devuelve status 'error' indicando que el command es desconocido.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import invoke_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_rejects_unknown_command():
    import handler

    # Act
    with patch('handler.ensure_database_url'):
        result = handler.lambda_handler(invoke_event('bogus'), lambda_context())

    # Assert
    assert result['status'] == 'error'
    assert result['error'] == "command desconocido: 'bogus'."
