"""Service stream_service.process_record — idempotencia.

Given un event_id ya registrado en processed_stream_events,
When se invoca process_record,
Then devuelve 'skipped' y no inserta ninguna fila.
"""

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record

pytestmark = pytest.mark.unit


@contextmanager
def _fake_session():
    yield object()


def test_service_skips_already_processed_event():
    from services import stream_service

    # Arrange
    with (
        patch.object(stream_service, 'db_session', _fake_session),
        patch.object(
            stream_service, 'is_event_processed', return_value=True
        ),
        patch.object(stream_service, 'insert_contact') as mock_insert,
        patch.object(stream_service, 'mark_event_processed') as mock_mark,
    ):
        # Act
        result = stream_service.process_record(
            contact_record('evt-dup'), 'evt-dup'
        )

    # Assert
    assert result == 'skipped'
    assert mock_insert.call_count == 0
    assert mock_mark.call_count == 0
