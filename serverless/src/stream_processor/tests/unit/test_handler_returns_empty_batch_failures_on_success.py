"""Handler — batch sin fallos.

Given un batch con un record INSERT de contacts que procesa bien,
When lambda_handler lo procesa,
Then devuelve {'batchItemFailures': []}.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record, lambda_context, stream_event

pytestmark = pytest.mark.unit


def test_handler_returns_empty_batch_failures_on_success():
    import handler

    # Arrange
    event = stream_event(contact_record('evt-1'))
    with patch(
        'controllers.stream.process.process_record',
        return_value='processed',
    ):
        # Act
        result = handler.lambda_handler(event, lambda_context())

    # Assert
    assert result == {'batchItemFailures': []}
