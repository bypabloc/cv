"""Tests del handler stream_processor (batch + batchItemFailures + ORM)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import pytest

from stream_processor import handler
from stream_processor.handler import lambda_handler

pytestmark = pytest.mark.unit

_CONTACTS_ARN = (
    'arn:aws:dynamodb:us-east-1:123:table/portfolio-contacts-dev/stream/x'
)
_TRACKING_ARN = (
    'arn:aws:dynamodb:us-east-1:123:table/portfolio-tracking-dev/stream/x'
)


@dataclass
class MockLambdaContext:
    """Context minimo para inject_lambda_context de Powertools."""

    function_name: str = 'test-stream'
    memory_limit_in_mb: int = 256
    invoked_function_arn: str = (
        'arn:aws:lambda:us-east-1:000000000000:function:stream'
    )
    aws_request_id: str = 'test-req-id'

    def get_remaining_time_in_millis(self) -> int:
        return 10000


def _ctx() -> Any:
    return MockLambdaContext()


def _contact_record(event_id: str) -> dict[str, Any]:
    """Stream record INSERT de la tabla contacts."""
    return {
        'eventID': event_id,
        'eventName': 'INSERT',
        'eventSourceARN': _CONTACTS_ARN,
        'dynamodb': {
            'NewImage': {
                'id': {'S': f'contact-{event_id}'},
                'name': {'S': 'Pablo'},
                'email': {'S': 'p@example.com'},
                'message': {'S': 'hola'},
                'created_at': {'S': '2026-05-17T00:00:00Z'},
            },
        },
    }


def _tracking_record(event_id: str) -> dict[str, Any]:
    """Stream record INSERT de la tabla tracking."""
    return {
        'eventID': event_id,
        'eventName': 'INSERT',
        'eventSourceARN': _TRACKING_ARN,
        'dynamodb': {
            'NewImage': {
                'session_id': {'S': f'sess-{event_id}'},
                'page_id': {'S': '019e372b-e0a7-7154-8279-8829bcf6a08c'},
                'page_url': {'S': 'https://the-full-stack.com/'},
                'created_at': {'S': '2026-05-17T00:00:00Z'},
            },
        },
    }


class _Recorder:
    """Captura las llamadas a pg_writer + db_session, simula fallos.

    `db_session()` real abre una Session y hace commit/rollback. Aqui el
    context manager fake cuenta commits (salida limpia) y rollbacks
    (salida por excepcion) para verificar el control de transaccion.
    """

    def __init__(self, fail_on: set[str] | None = None) -> None:
        self.processed_log: set[str] = set()
        self.inserts: list[dict[str, Any]] = []
        self.commits = 0
        self.rollbacks = 0
        self.marked: list[str] = []
        self._fail_on = fail_on or set()

    @contextmanager
    def db_session(self) -> Iterator[object]:
        """Context manager fake: commit al salir limpio, rollback si excepcion."""
        session = object()
        try:
            yield session
            self.commits += 1
        except Exception:
            self.rollbacks += 1
            raise

    def is_event_processed(self, _session: object, event_id: str) -> bool:
        return event_id in self.processed_log

    def insert_contact(
        self, _session: object, payload: dict[str, Any]
    ) -> None:
        if payload.get('id') in self._fail_on:
            raise RuntimeError('simulated contact write failure')
        self.inserts.append(payload)

    def insert_tracking(
        self, _session: object, payload: dict[str, Any]
    ) -> None:
        if payload.get('session_id') in self._fail_on:
            raise RuntimeError('simulated tracking write failure')
        self.inserts.append(payload)

    def mark_event_processed(
        self,
        _session: object,
        event_id: str,
        *,
        event_type: str,
        table_name: str,
    ) -> None:
        _ = (event_type, table_name)
        self.marked.append(event_id)
        self.processed_log.add(event_id)


def _wire_recorder(
    monkeypatch: pytest.MonkeyPatch, recorder: _Recorder
) -> None:
    """Sustituye db_session + las funciones pg_writer del handler."""
    monkeypatch.setattr(handler, 'db_session', recorder.db_session)
    monkeypatch.setattr(
        handler, 'is_event_processed', recorder.is_event_processed
    )
    monkeypatch.setattr(handler, 'insert_contact', recorder.insert_contact)
    monkeypatch.setattr(handler, 'insert_tracking', recorder.insert_tracking)
    monkeypatch.setattr(
        handler, 'mark_event_processed', recorder.mark_event_processed
    )


class TestStreamHandlerHappyPath:
    """lambda_handler - batch sin fallos."""

    def test_when_contact_record_then_processed_and_committed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un batch con un record INSERT de contacts [AC-4],
        When lambda_handler lo procesa,
        Then el contacto se inserta, la Session commitea y no hay
        batchItemFailures.
        """
        # Arrange
        recorder = _Recorder()
        _wire_recorder(monkeypatch, recorder)
        event = {'Records': [_contact_record('evt-1')]}

        # Act
        response = lambda_handler(event, _ctx())

        # Assert
        assert response == {'batchItemFailures': []}
        assert recorder.commits == 1
        assert recorder.marked == ['evt-1']

    def test_when_tracking_record_then_processed_and_committed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un batch con un record INSERT de tracking [AC-4],
        When lambda_handler lo procesa,
        Then el evento se inserta, la Session commitea y no hay
        batchItemFailures.
        """
        # Arrange
        recorder = _Recorder()
        _wire_recorder(monkeypatch, recorder)
        event = {'Records': [_tracking_record('evt-2')]}

        # Act
        response = lambda_handler(event, _ctx())

        # Assert
        assert response == {'batchItemFailures': []}
        assert recorder.commits == 1
        assert len(recorder.inserts) == 1

    def test_when_empty_batch_then_no_failures(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un batch sin records [AC-4],
        When lambda_handler lo procesa,
        Then retorna batchItemFailures vacio y no hay commits.
        """
        # Arrange
        recorder = _Recorder()
        _wire_recorder(monkeypatch, recorder)

        # Act
        response = lambda_handler({'Records': []}, _ctx())

        # Assert
        assert response == {'batchItemFailures': []}
        assert recorder.commits == 0


class TestStreamHandlerIdempotency:
    """lambda_handler - idempotencia: evento ya procesado se saltea."""

    def test_when_event_already_processed_then_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un event_id ya registrado en processed_stream_events [AC-5],
        When el handler lo recibe de nuevo,
        Then NO se inserta de nuevo (la fila no se duplica).
        """
        # Arrange
        recorder = _Recorder()
        recorder.processed_log.add('evt-dup')
        _wire_recorder(monkeypatch, recorder)
        event = {'Records': [_tracking_record('evt-dup')]}

        # Act
        response = lambda_handler(event, _ctx())

        # Assert: ningun insert; la Session abrio y cerro limpia (commit
        # de un no-op) pero no se duplico la fila.
        assert response == {'batchItemFailures': []}
        assert recorder.inserts == []

    def test_when_same_record_twice_then_second_pass_does_not_duplicate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given el mismo record entregado en dos invocaciones [AC-5],
        When lambda_handler procesa la 2a vez,
        Then solo hay un insert total (la 2a pasada lo saltea por
        idempotencia).
        """
        # Arrange
        recorder = _Recorder()
        _wire_recorder(monkeypatch, recorder)
        event = {'Records': [_contact_record('evt-once')]}

        # Act: dos invocaciones con el mismo record
        lambda_handler(event, _ctx())
        lambda_handler(event, _ctx())

        # Assert: el mark de la 1a pasada hace que la 2a lo saltee
        assert len(recorder.inserts) == 1


class TestStreamHandlerBatchFailures:
    """lambda_handler - un record OK + uno que falla -> batchItemFailures."""

    def test_when_one_record_fails_then_only_failed_reported(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un batch con un record OK y otro que falla al escribir [AC-4],
        When lambda_handler procesa el batch,
        Then batchItemFailures reporta solo el itemIdentifier del fallido.
        """
        # Arrange: el record 'evt-bad' falla; 'evt-ok' procesa bien
        recorder = _Recorder(fail_on={'contact-evt-bad'})
        _wire_recorder(monkeypatch, recorder)
        event = {
            'Records': [
                _contact_record('evt-ok'),
                _contact_record('evt-bad'),
            ]
        }

        # Act
        response = lambda_handler(event, _ctx())

        # Assert: solo el fallido en batchItemFailures
        assert response == {
            'batchItemFailures': [{'itemIdentifier': 'evt-bad'}]
        }
        # el OK avanzo: 1 insert + 1 commit; el fallido hizo rollback
        assert len(recorder.inserts) == 1
        assert recorder.commits == 1
        assert recorder.rollbacks == 1

    def test_when_record_fails_then_rollback_called(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un record cuya escritura a PG lanza excepcion [AC-4],
        When lambda_handler lo procesa,
        Then la Session hace rollback y el record entra en batchItemFailures.
        """
        # Arrange
        recorder = _Recorder(fail_on={'sess-evt-fail'})
        _wire_recorder(monkeypatch, recorder)
        event = {'Records': [_tracking_record('evt-fail')]}

        # Act
        response = lambda_handler(event, _ctx())

        # Assert
        assert response == {
            'batchItemFailures': [{'itemIdentifier': 'evt-fail'}]
        }
        assert recorder.rollbacks == 1
        assert recorder.commits == 0


class TestStreamHandlerSkippedRecords:
    """lambda_handler - records que se saltean (sin eventID, MODIFY, ARN)."""

    def test_when_record_has_no_event_id_then_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un record sin eventID [AC-4],
        When lambda_handler lo procesa,
        Then se saltea (ni siquiera abre Session) y no entra en
        batchItemFailures.
        """
        # Arrange
        recorder = _Recorder()
        _wire_recorder(monkeypatch, recorder)
        record = _contact_record('')
        record['eventID'] = ''

        # Act
        response = lambda_handler({'Records': [record]}, _ctx())

        # Assert
        assert response == {'batchItemFailures': []}
        assert recorder.commits == 0

    def test_when_record_is_modify_then_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un record MODIFY de contacts [AC-4],
        When lambda_handler lo procesa,
        Then parse_contact_record devuelve None y el record se saltea.
        """
        # Arrange
        recorder = _Recorder()
        _wire_recorder(monkeypatch, recorder)
        record = _contact_record('evt-modify')
        record['eventName'] = 'MODIFY'

        # Act
        response = lambda_handler({'Records': [record]}, _ctx())

        # Assert: MODIFY -> parse devuelve None -> sin insert
        assert response == {'batchItemFailures': []}
        assert recorder.inserts == []

    def test_when_record_arn_unknown_then_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un record cuyo ARN no es contacts ni tracking [AC-4],
        When lambda_handler lo procesa,
        Then detect_table devuelve 'unknown' y el record se saltea.
        """
        # Arrange
        recorder = _Recorder()
        _wire_recorder(monkeypatch, recorder)
        record = _contact_record('evt-unknown')
        record['eventSourceARN'] = (
            'arn:aws:dynamodb:us-east-1:123:table/other-table/stream/x'
        )

        # Act
        response = lambda_handler({'Records': [record]}, _ctx())

        # Assert
        assert response == {'batchItemFailures': []}
        assert recorder.inserts == []

    def test_when_tracking_record_missing_keys_then_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un record tracking sin session_id en el NewImage [AC-4],
        When lambda_handler lo procesa,
        Then parse_tracking_record devuelve None y el record se saltea.
        """
        # Arrange
        recorder = _Recorder()
        _wire_recorder(monkeypatch, recorder)
        record = _tracking_record('evt-nokeys')
        del record['dynamodb']['NewImage']['session_id']

        # Act
        response = lambda_handler({'Records': [record]}, _ctx())

        # Assert
        assert response == {'batchItemFailures': []}
        assert recorder.inserts == []
