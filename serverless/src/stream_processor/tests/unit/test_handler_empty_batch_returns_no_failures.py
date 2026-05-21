"""Handler — batch vacio.

Given un evento Stream sin records,
When lambda_handler lo procesa,
Then devuelve {'batchItemFailures': []} sin delegar al service.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import lambda_context, stream_event

pytestmark = pytest.mark.unit


def test_handler_empty_batch_returns_no_failures():
    import handler

    # Arrange
    with patch(
        'controllers.stream.process.process_record'
    ) as mock_process:
        # Act
        result = handler.lambda_handler(stream_event(), lambda_context())

    # Assert
    assert result == {'batchItemFailures': []}
    assert mock_process.call_count == 0
