"""Handler — downgrade sin 'confirm'.

Given un payload {command: 'downgrade', args: {target: '-1'}} sin confirm,
When lambda_handler lo procesa,
Then el controller rechaza y el handler devuelve status 'error'.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import invoke_event, lambda_context

pytestmark = pytest.mark.unit


def test_handler_downgrade_without_confirm_returns_error():
    import handler

    # Act
    with patch('handler.ensure_database_url'):
        result = handler.lambda_handler(
            invoke_event('downgrade', {'target': '-1'}),
            lambda_context(),
        )

    # Assert
    assert result['status'] == 'error'
    assert result['command'] == 'downgrade'
    assert 'confirm' in result['error']
