"""E2E — batch vacio.

Given un evento Stream sin records (`{Records: []}`),
When `lambda_handler` procesa el batch end-to-end,
Then el handler devuelve `batchItemFailures` vacio y nada se escribe en
  la base.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent, TrackingEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import stream_event
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_empty_batch_no_failures_e2e(sqlite_db: Engine) -> None:
    # Arrange
    event = stream_event()

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    assert session.query(Contact).count() == 0
    assert session.query(TrackingEvent).count() == 0
    assert session.query(ProcessedStreamEvent).count() == 0
    session.close()
