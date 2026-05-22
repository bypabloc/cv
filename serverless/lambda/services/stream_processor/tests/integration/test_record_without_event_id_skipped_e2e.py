"""E2E — record sin eventID.

Given un Stream record sin la clave `eventID`,
When `lambda_handler` procesa el batch end-to-end,
Then el controller lo saltea sin delegar al service: nada se replica y
  el handler devuelve `batchItemFailures` vacio.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import (
    contact_record_without_event_id,
    stream_event,
)
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_record_without_event_id_skipped_e2e(sqlite_db: Engine) -> None:
    # Arrange
    event = stream_event(contact_record_without_event_id())

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    assert session.query(Contact).count() == 0
    assert session.query(ProcessedStreamEvent).count() == 0
    session.close()
