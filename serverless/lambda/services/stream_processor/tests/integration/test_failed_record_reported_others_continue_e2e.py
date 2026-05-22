"""E2E — record que falla al insertar; los demas del batch siguen.

Given un batch con un record INSERT de `contacts` valido, otro con
  `created_at` malformado (falla al parsear -> excepcion) y un tercero
  INSERT de `tracking` valido,
When `lambda_handler` procesa el batch end-to-end,
Then el record fallido se reporta en `batchItemFailures` por su
  `eventID`, los otros dos se replican normalmente a sus tablas y el
  fallo de uno NO aborta el procesamiento de los demas.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent, TrackingEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import (
    contact_id,
    contact_record,
    invalid_contact_record,
    stream_event,
    tracking_record,
)
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_failed_record_reported_others_continue_e2e(
    sqlite_db: Engine,
) -> None:
    # Arrange
    event = stream_event(
        contact_record('ok-contact'),
        invalid_contact_record('bad-contact'),
        tracking_record('ok-tracking'),
    )

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {
        'batchItemFailures': [{'itemIdentifier': 'bad-contact'}],
    }

    session = Session(sqlite_db)
    # Los dos records validos se replicaron pese al fallo del tercero.
    assert session.query(Contact).count() == 1
    assert session.query(Contact).first().id == contact_id('ok-contact')
    assert session.query(TrackingEvent).count() == 1

    processed_ids = sorted(
        row.event_id for row in session.query(ProcessedStreamEvent).all()
    )
    assert processed_ids == ['ok-contact', 'ok-tracking']
    session.close()
