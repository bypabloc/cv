"""Tests de stream_processor.pg_writer (escritura ORM a la replica Neon)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from shared.db.models import Contact, ProcessedStreamEvent, TrackingEvent
from stream_processor import pg_writer

pytestmark = pytest.mark.unit


class _FakeResult:
    """Resultado fake de `Session.execute` — controla lo que `first()` da."""

    def __init__(self, row: Any) -> None:
        self._row = row

    def first(self) -> Any:
        return self._row


class _FakeSession:
    """Session fake: captura los objetos `add()` y la query de `execute()`."""

    def __init__(self, *, exists: bool = False) -> None:
        self.added: list[Any] = []
        self.executed: list[Any] = []
        # `(1,)` si el evento existe; `None` si no — replica lo que devuelve
        # un `SELECT event_id WHERE ...` real.
        self._first_row: Any = (1,) if exists else None

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def execute(self, stmt: Any) -> _FakeResult:
        self.executed.append(stmt)
        return _FakeResult(self._first_row)


def _tracking_payload(**overrides: Any) -> dict[str, Any]:
    """Payload de tracking minimo para `insert_tracking`, con overrides."""
    payload: dict[str, Any] = {
        'session_id': 'sess-3',
        'page_id': '019e372b-e0a7-7154-8279-8829bcf6a08c',
        'stream_event_id': 'evt-200',
        'created_at': datetime(2026, 5, 17, tzinfo=UTC),
        'expires_at': datetime(2026, 7, 17, tzinfo=UTC),
        'page_url': 'https://the-full-stack.com/',
        'page_title': None,
        'page_path': None,
        'referrer': None,
        'utm_source': None,
        'utm_medium': None,
        'utm_campaign': None,
        'utm_content': None,
        'utm_term': None,
        'viewport_width': None,
        'viewport_height': None,
        'niche': 'generic',
        'event_id': 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
        'event_type_id': '019e372b-e0a7-7154-8279-8829bcf6a08c',
        'event_props': None,
        'ip': None,
        'country': None,
        'user_agent': None,
        'browser': None,
        'browser_version': None,
        'os': None,
        'device_type': None,
    }
    payload.update(overrides)
    return payload


class TestInsertTracking:
    """insert_tracking - agrega un TrackingEvent mapeado a la Session."""

    def test_when_payload_given_then_adds_tracking_event(self) -> None:
        """
        Given un payload de tracking con event_id y event_type_id,
        When insert_tracking lo procesa,
        Then se agrega a la Session un TrackingEvent con esos valores.
        """
        session = _FakeSession()

        pg_writer.insert_tracking(session, _tracking_payload())

        assert len(session.added) == 1
        event = session.added[0]
        assert isinstance(event, TrackingEvent)
        assert event.event_id == 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
        assert event.event_type_id == '019e372b-e0a7-7154-8279-8829bcf6a08c'

    def test_when_event_props_present_then_set_on_model(self) -> None:
        """
        Given event_props como dict en el payload,
        When insert_tracking lo procesa,
        Then el TrackingEvent lleva event_props como dict (SQLAlchemy lo
        adapta a JSONB sin envoltura manual).
        """
        session = _FakeSession()
        props = {'depth': 50, 'href': 'https://x.com'}

        pg_writer.insert_tracking(
            session, _tracking_payload(event_props=props)
        )

        assert session.added[0].event_props == props

    def test_when_event_props_none_then_stays_none(self) -> None:
        """
        Given un payload sin event_props (None),
        When insert_tracking lo procesa,
        Then el TrackingEvent lleva event_props en None.
        """
        session = _FakeSession()

        pg_writer.insert_tracking(
            session, _tracking_payload(event_props=None)
        )

        assert session.added[0].event_props is None


class TestInsertContact:
    """insert_contact - agrega un Contact mapeado a la Session."""

    def test_when_payload_given_then_adds_contact(self) -> None:
        """
        Given un payload de contacto,
        When insert_contact lo procesa,
        Then se agrega a la Session un Contact con el id del payload.
        """
        session = _FakeSession()

        pg_writer.insert_contact(session, {'id': 'contact-uuid'})

        assert len(session.added) == 1
        assert isinstance(session.added[0], Contact)
        assert session.added[0].id == 'contact-uuid'

    def test_when_payload_has_session_id_then_set_on_model(self) -> None:
        """
        Given un payload de contacto con session_id,
        When insert_contact lo procesa,
        Then el Contact lleva session_id (correlacion con tracking_events).
        """
        session = _FakeSession()

        pg_writer.insert_contact(
            session, {'id': 'contact-uuid', 'session_id': 'a' * 32}
        )

        assert session.added[0].session_id == 'a' * 32

    def test_when_legacy_fields_null_then_set_none_on_model(self) -> None:
        """
        Given un payload de contacto con ip/country/user_agent en NULL,
        When insert_contact lo procesa,
        Then el Contact lleva esas columnas legacy en None.
        """
        session = _FakeSession()
        payload = {
            'id': 'contact-uuid',
            'stream_event_id': 'evt-1',
            'created_at': datetime(2026, 5, 17, tzinfo=UTC),
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'hola',
            'company': None,
            'role': None,
            'service_type': None,
            'budget': None,
            'timeline': None,
            'niche': 'generic',
            'session_id': 'a' * 32,
            'ip': None,
            'country': None,
            'user_agent': None,
        }

        pg_writer.insert_contact(session, payload)

        contact = session.added[0]
        assert contact.ip is None
        assert contact.country is None
        assert contact.user_agent is None


class TestIdempotencyLog:
    """is_event_processed + mark_event_processed - log de idempotencia."""

    def test_when_event_in_log_then_is_processed_true(self) -> None:
        """
        Given un event_id ya registrado en processed_stream_events,
        When is_event_processed lo consulta,
        Then retorna True (el handler lo saltea, no duplica la fila).
        """
        session = _FakeSession(exists=True)

        assert pg_writer.is_event_processed(session, 'evt-done') is True

    def test_when_event_not_in_log_then_is_processed_false(self) -> None:
        """
        Given un event_id que no esta en processed_stream_events,
        When is_event_processed lo consulta,
        Then retorna False.
        """
        session = _FakeSession(exists=False)

        assert pg_writer.is_event_processed(session, 'evt-new') is False

    def test_when_mark_processed_then_adds_processed_stream_event(
        self,
    ) -> None:
        """
        Given un event_id procesado,
        When mark_event_processed lo registra,
        Then se agrega a la Session un ProcessedStreamEvent con event_type
        y table_name.
        """
        session = _FakeSession()

        pg_writer.mark_event_processed(
            session, 'evt-1', event_type='INSERT', table_name='tracking'
        )

        assert len(session.added) == 1
        row = session.added[0]
        assert isinstance(row, ProcessedStreamEvent)
        assert row.event_id == 'evt-1'
        assert row.event_type == 'INSERT'
        assert row.table_name == 'tracking'
