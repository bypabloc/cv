"""E2E — record de tabla desconocida.

Given un Stream record cuyo `eventSourceARN` no matchea ni
  `portfolio-contacts-` ni `portfolio-tracking-`,
When `lambda_handler` procesa el batch end-to-end,
Then `detect_table` devuelve `'unknown'`: el record se saltea, nada se
  replica, no queda rastro en `processed_stream_events` y el handler
  devuelve `batchItemFailures` vacio.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent, TrackingEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import (
    stream_event,
    unknown_table_record,
)
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_unknown_table_record_skipped_e2e(sqlite_db: Engine) -> None:
    # Arrange
    event = stream_event(unknown_table_record('unknown-evt-1'))

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    assert session.query(Contact).count() == 0
    assert session.query(TrackingEvent).count() == 0
    assert session.query(ProcessedStreamEvent).count() == 0
    session.close()
