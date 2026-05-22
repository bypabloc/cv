"""E2E — record REMOVE (no INSERT).

Given un Stream record con `eventName == 'REMOVE'` de la tabla
  `tracking` (borrado por TTL de DynamoDB),
When `lambda_handler` procesa el batch end-to-end,
Then `parse_tracking_record` devuelve `None`: el record se saltea, nada
  se inserta en `tracking_events`, no queda rastro en
  `processed_stream_events` y el handler devuelve `batchItemFailures`
  vacio.
"""

from __future__ import annotations

import pytest
from shared.db.models import ProcessedStreamEvent, TrackingEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import remove_record, stream_event
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_remove_record_skipped_e2e(sqlite_db: Engine) -> None:
    # Arrange
    event = stream_event(remove_record('remove-evt-1'))

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    assert session.query(TrackingEvent).count() == 0
    assert session.query(ProcessedStreamEvent).count() == 0
    session.close()
