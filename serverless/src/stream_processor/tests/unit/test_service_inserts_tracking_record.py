"""Service stream_service.process_record — INSERT de tracking event.

Given un Stream record INSERT de la tabla tracking no procesado,
When se invoca process_record,
Then devuelve 'processed', inserta el evento y marca el event_id.
"""

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from tests.unit._helpers import tracking_record

pytestmark = pytest.mark.unit


@contextmanager
def _fake_session():
    yield object()


def test_service_inserts_tracking_record():
    from services import stream_service

    # Arrange
    with (
        patch.object(stream_service, 'db_session', _fake_session),
        patch.object(
            stream_service, 'is_event_processed', return_value=False
        ),
        patch.object(stream_service, 'insert_contact') as mock_contact,
        patch.object(stream_service, 'insert_tracking') as mock_tracking,
        patch.object(stream_service, 'mark_event_processed') as mock_mark,
    ):
        # Act
        result = stream_service.process_record(
            tracking_record('evt-trk'), 'evt-trk'
        )

    # Assert
    assert result == 'processed'
    assert mock_tracking.call_count == 1
    assert mock_contact.call_count == 0
    assert mock_mark.call_count == 1
