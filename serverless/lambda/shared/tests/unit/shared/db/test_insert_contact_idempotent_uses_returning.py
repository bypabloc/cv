"""shared.db.repository.insert_contact_idempotent — bug del 26/05/2026.

Given el statement INSERT ... ON CONFLICT DO NOTHING genera RETURNING id,
When la fila SE inserta (no hay conflicto),
Then `result.first()` devuelve la fila y la funcion retorna True.

Given el statement INSERT ... ON CONFLICT DO NOTHING genera RETURNING id,
When la fila YA existia (conflict),
Then `result.first()` devuelve None y la funcion retorna False.

Por que: confiar en `result.rowcount` con `on_conflict_do_nothing` reporta
0 incluso cuando la fila SI se inserto (verificado en runtime con Neon).
La forma robusta es agregar `RETURNING id` al statement y contar las
filas devueltas. Sin este fix, el flujo de contacto reportaria "already
persisted" SIEMPRE aunque la fila se haya insertado.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repository import (
    insert_contact_idempotent,
    insert_tracking_idempotent,
)

pytestmark = pytest.mark.unit


def test_insert_contact_idempotent_returns_true_when_row_inserted() -> None:
    """Si RETURNING devuelve una fila, la funcion devuelve True."""
    # Arrange
    session = MagicMock()
    result_mock = MagicMock()
    result_mock.first.return_value = ('019e6672-af07-7d04-8154-53571b118c31',)
    session.execute.return_value = result_mock

    payload = {
        'id': '019e6672-af07-7d04-8154-53571b118c31',
        'name': 'Pablo',
        'email': 'user@example.com',
        'message': 'hola',
        'session_id': 'cf-session-1',
    }

    # Act
    persisted = insert_contact_idempotent(session, payload)

    # Assert
    assert persisted is True
    # Statement compilado debe incluir RETURNING (no rowcount).
    stmt = session.execute.call_args[0][0]
    compiled = str(stmt.compile())
    assert 'RETURNING' in compiled.upper()
    assert 'ON CONFLICT' in compiled.upper()


def test_insert_contact_idempotent_returns_false_when_conflict() -> None:
    """Si RETURNING no devuelve fila (ON CONFLICT DO NOTHING), False."""
    # Arrange
    session = MagicMock()
    result_mock = MagicMock()
    result_mock.first.return_value = None
    session.execute.return_value = result_mock

    payload = {
        'id': '019e6672-af07-7d04-8154-53571b118c31',
        'name': 'Pablo',
        'email': 'user@example.com',
        'message': 'hola',
        'session_id': 'cf-session-1',
    }

    # Act
    persisted = insert_contact_idempotent(session, payload)

    # Assert
    assert persisted is False


def test_insert_tracking_idempotent_returns_true_when_row_inserted() -> None:
    """Si RETURNING devuelve una fila, la funcion devuelve True."""
    # Arrange
    from datetime import UTC, datetime

    session = MagicMock()
    result_mock = MagicMock()
    result_mock.first.return_value = (datetime(2026, 5, 26, tzinfo=UTC),)
    session.execute.return_value = result_mock

    payload = {
        'session_id': 'cf-session-1',
        'visit_id': 'visit-1',
        'page_id': 'page-1',
        'created_at': datetime(2026, 5, 26, tzinfo=UTC),
        'event_props': {},
    }

    # Act
    persisted = insert_tracking_idempotent(session, payload)

    # Assert
    assert persisted is True
    stmt = session.execute.call_args[0][0]
    # No `literal_binds=True`: TrackingEvent.event_props (JSONB) no se
    # puede serializar a literal. Sin literal_binds basta para validar
    # RETURNING + ON CONFLICT en el SQL generado.
    compiled = str(stmt.compile())
    assert 'RETURNING' in compiled.upper()
    assert 'ON CONFLICT' in compiled.upper()


def test_insert_tracking_idempotent_returns_false_when_conflict() -> None:
    """Si RETURNING no devuelve fila, False."""
    # Arrange
    from datetime import UTC, datetime

    session = MagicMock()
    result_mock = MagicMock()
    result_mock.first.return_value = None
    session.execute.return_value = result_mock

    payload = {
        'session_id': 'cf-session-1',
        'visit_id': 'visit-1',
        'page_id': 'page-1',
        'created_at': datetime(2026, 5, 26, tzinfo=UTC),
        'event_props': {},
    }

    # Act
    persisted = insert_tracking_idempotent(session, payload)

    # Assert
    assert persisted is False
