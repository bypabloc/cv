"""E2E — record MODIFY (no INSERT).

Given un Stream record con `eventName == 'MODIFY'` de la tabla
  `contacts`,
When `lambda_handler` procesa el batch end-to-end,
Then `parse_contact_record` devuelve `None` (solo se replican los
  INSERT): el record se saltea, nada se inserta en `contacts`, pero el
  evento queda registrado en `processed_stream_events` y el handler
  devuelve `batchItemFailures` vacio.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import modify_record, stream_event
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_modify_record_skipped_e2e(sqlite_db: Engine) -> None:
    # Arrange
    event = stream_event(modify_record('modify-evt-1'))

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    assert session.query(Contact).count() == 0
    # parse_* devuelve None ANTES de mark_event_processed: el MODIFY no
    # deja rastro en processed_stream_events.
    assert session.query(ProcessedStreamEvent).count() == 0
    session.close()
