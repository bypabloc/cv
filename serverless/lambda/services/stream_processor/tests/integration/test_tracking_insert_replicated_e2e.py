"""E2E — INSERT de tracking replicado a la base.

Given un evento Stream con un record INSERT de la tabla `tracking`,
When `lambda_handler` procesa el batch end-to-end,
Then la fila se replica en `tracking_events`, se registra en
  `processed_stream_events` y el handler devuelve `batchItemFailures`
  vacio.
"""

from __future__ import annotations

import pytest
from shared.db.models import ProcessedStreamEvent, TrackingEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import stream_event, tracking_record
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_tracking_insert_replicated_e2e(sqlite_db: Engine) -> None:
    # Arrange
    event = stream_event(tracking_record('tracking-evt-1'))

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    events = session.query(TrackingEvent).all()
    assert len(events) == 1
    assert events[0].session_id == 'sess-tracking-evt-1'
    assert events[0].page_id == '019e372b-e0a7-7154-8279-8829bcf6a08c'
    assert events[0].page_url == 'https://the-full-stack.com/'
    assert events[0].page_title == 'Home'
    assert events[0].niche == 'generic'
    assert events[0].viewport_width == 1920
    assert events[0].stream_event_id == 'tracking-evt-1'

    processed = session.query(ProcessedStreamEvent).all()
    assert len(processed) == 1
    assert processed[0].event_id == 'tracking-evt-1'
    assert processed[0].event_type == 'INSERT'
    assert processed[0].table_name == 'tracking'
    session.close()
