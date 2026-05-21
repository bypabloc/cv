"""Service stream_service.process_record — INSERT de contacto.

Given un Stream record INSERT de la tabla contacts no procesado,
When se invoca process_record,
Then devuelve 'processed', inserta el contacto y marca el evento.
"""

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record

pytestmark = pytest.mark.unit


@contextmanager
def _fake_session():
    yield object()


def test_service_inserts_contact_record():
    from services import stream_service

    # Arrange
    with (
        patch.object(stream_service, 'db_session', _fake_session),
        patch.object(
            stream_service, 'is_event_processed', return_value=False
        ),
        patch.object(stream_service, 'insert_contact') as mock_insert,
        patch.object(stream_service, 'insert_tracking') as mock_tracking,
        patch.object(stream_service, 'mark_event_processed') as mock_mark,
    ):
        # Act
        result = stream_service.process_record(
            contact_record('evt-ok'), 'evt-ok'
        )

    # Assert
    assert result == 'processed'
    assert mock_insert.call_count == 1
    assert mock_tracking.call_count == 0
    assert mock_mark.call_count == 1
