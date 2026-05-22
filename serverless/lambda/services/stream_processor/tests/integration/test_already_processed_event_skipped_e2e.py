"""E2E — record con eventID ya procesado (idempotencia).

Given un Stream record cuyo `eventID` ya esta en
  `processed_stream_events`,
When `lambda_handler` procesa el batch end-to-end,
Then el record se saltea: NO se re-inserta en `contacts` y el handler
  devuelve `batchItemFailures` vacio.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.db import seed_processed_event
from tests.integration._fixtures.events import contact_record, stream_event
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_already_processed_event_skipped_e2e(sqlite_db: Engine) -> None:
    # Arrange — el evento ya fue procesado en una invocacion previa.
    seed_processed_event(sqlite_db, 'dup-evt-1')
    event = stream_event(contact_record('dup-evt-1'))

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    assert session.query(Contact).count() == 0
    assert session.query(ProcessedStreamEvent).count() == 1
    session.close()
