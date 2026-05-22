"""Handler — fallo inesperado del controller.

Given un batch con records y un run_controller que lanza una excepcion,
When lambda_handler lo procesa,
Then reporta TODOS los records como batchItemFailures (AWS reintenta).
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record, lambda_context, stream_event

pytestmark = pytest.mark.unit


def test_handler_reports_all_failed_when_controller_raises():
    import handler

    # Arrange
    event = stream_event(contact_record('evt-1'), contact_record('evt-2'))
    with patch.object(
        handler, 'run_controller', side_effect=RuntimeError('boom')
    ):
        # Act
        result = handler.lambda_handler(event, lambda_context())

    # Assert
    assert result == {
        'batchItemFailures': [
            {'itemIdentifier': 'evt-1'},
            {'itemIdentifier': 'evt-2'},
        ],
    }
