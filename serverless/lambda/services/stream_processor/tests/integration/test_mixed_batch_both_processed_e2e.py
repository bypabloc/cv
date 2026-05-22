"""E2E — batch mixto contact + tracking.

Given un evento Stream con un record INSERT de `contacts` y otro de
  `tracking` en el mismo batch,
When `lambda_handler` procesa el batch end-to-end,
Then ambas filas se replican a sus tablas, ambas quedan registradas en
  `processed_stream_events` y el handler devuelve `batchItemFailures`
  vacio.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent, TrackingEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import (
    contact_record,
    stream_event,
    tracking_record,
)
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_mixed_batch_both_processed_e2e(sqlite_db: Engine) -> None:
    # Arrange
    event = stream_event(
        contact_record('mixed-contact'),
        tracking_record('mixed-tracking'),
    )

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    assert session.query(Contact).count() == 1
    assert session.query(TrackingEvent).count() == 1

    processed_ids = sorted(
        row.event_id for row in session.query(ProcessedStreamEvent).all()
    )
    assert processed_ids == ['mixed-contact', 'mixed-tracking']
    session.close()
