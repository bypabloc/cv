"""E2E — INSERT de contacts replicado a la base.

Given un evento Stream con un record INSERT de la tabla `contacts`,
When `lambda_handler` procesa el batch end-to-end (handler -> controller
  -> service -> ORM -> DB),
Then la fila se replica en `contacts`, se registra en
  `processed_stream_events` y el handler devuelve `batchItemFailures`
  vacio.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import (
    contact_id,
    contact_record,
    stream_event,
)
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_contact_insert_replicated_e2e(sqlite_db: Engine) -> None:
    # Arrange
    event = stream_event(contact_record('contact-evt-1'))

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    contacts = session.query(Contact).all()
    assert len(contacts) == 1
    assert contacts[0].id == contact_id('contact-evt-1')
    assert contacts[0].name == 'Pablo'
    assert contacts[0].email == 'p@example.com'
    assert contacts[0].message == 'hola'
    assert contacts[0].company == 'Acme'
    assert contacts[0].stream_event_id == 'contact-evt-1'
    assert contacts[0].session_id == 'sess-contact-evt-1'

    processed = session.query(ProcessedStreamEvent).all()
    assert len(processed) == 1
    assert processed[0].event_id == 'contact-evt-1'
    assert processed[0].event_type == 'INSERT'
    assert processed[0].table_name == 'contacts'
    session.close()
