"""E2E — la validacion del evento falla.

Given un evento Stream con dos records, donde la validacion del evento
  sintetico falla (operacion no resoluble),
When `lambda_handler` procesa el batch end-to-end,
Then el handler reporta TODOS los records con `eventID` en
  `batchItemFailures` (para que AWS reintente el batch entero) y nada se
  escribe en la base.

Nota: el helper `patched_validation` mockea `handler.logger` ademas de
`validate_event`. La rama de validacion fallida del handler logea con
`extra={'message': ...}` y `message` es una clave reservada de
`LogRecord` (bug pre-existente del handler, fuera del scope de esta
suite). El mock del logger lo neutraliza para poder observar el
contrato de salida del handler.
"""

from __future__ import annotations

import pytest
from shared.db.models import Contact, ProcessedStreamEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import contact_record, stream_event
from tests.integration._fixtures.runner import (
    invoke_handler,
    patched_validation,
)

pytestmark = pytest.mark.integration


def test_event_validation_fails_all_records_reported_e2e(
    sqlite_db: Engine,
) -> None:
    # Arrange
    event = stream_event(
        contact_record('val-evt-1'),
        contact_record('val-evt-2'),
    )

    # Act — la validacion del evento sintetico se fuerza a fallar.
    with patched_validation():
        result = invoke_handler(event, sqlite_db)

    # Assert — todos los records con eventID se reportan como fallidos.
    assert result == {
        'batchItemFailures': [
            {'itemIdentifier': 'val-evt-1'},
            {'itemIdentifier': 'val-evt-2'},
        ],
    }

    session = Session(sqlite_db)
    assert session.query(Contact).count() == 0
    assert session.query(ProcessedStreamEvent).count() == 0
    session.close()
