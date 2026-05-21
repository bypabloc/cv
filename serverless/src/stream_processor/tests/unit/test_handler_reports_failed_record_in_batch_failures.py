"""Handler — un record OK y otro que falla.

Given un batch con un record OK y otro cuyo procesamiento lanza excepcion,
When lambda_handler procesa el batch,
Then batchItemFailures reporta solo el itemIdentifier del fallido.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record, lambda_context, stream_event

pytestmark = pytest.mark.unit


def _process_side_effect(record, event_id):
    if event_id == 'evt-bad':
        raise RuntimeError('simulated write failure')
    return 'processed'


def test_handler_reports_failed_record_in_batch_failures():
    import handler

    # Arrange
    event = stream_event(
        contact_record('evt-ok'), contact_record('evt-bad')
    )
    with patch(
        'controllers.stream.process.process_record',
        side_effect=_process_side_effect,
    ):
        # Act
        result = handler.lambda_handler(event, lambda_context())

    # Assert
    assert result == {
        'batchItemFailures': [{'itemIdentifier': 'evt-bad'}],
    }
