"""Service stream_service.process_record — tabla origen desconocida.

Given un Stream record cuyo eventSourceARN no es contacts ni tracking,
When se invoca process_record,
Then detect_table devuelve 'unknown' y el record se saltea.
"""

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record

pytestmark = pytest.mark.unit


@contextmanager
def _fake_session():
    yield object()


def test_service_skips_unknown_table_record():
    from services import stream_service

    # Arrange
    record = contact_record('evt-unknown')
    record['eventSourceARN'] = (
        'arn:aws:dynamodb:us-east-1:123:table/other-table/stream/x'
    )

    with (
        patch.object(stream_service, 'db_session', _fake_session),
        patch.object(
            stream_service, 'is_event_processed', return_value=False
        ),
        patch.object(stream_service, 'insert_contact') as mock_insert,
        patch.object(stream_service, 'mark_event_processed') as mock_mark,
    ):
        # Act
        result = stream_service.process_record(record, 'evt-unknown')

    # Assert
    assert result == 'skipped'
    assert mock_insert.call_count == 0
    assert mock_mark.call_count == 0
