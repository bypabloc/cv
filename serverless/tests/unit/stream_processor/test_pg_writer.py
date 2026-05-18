"""Tests de stream_processor.pg_writer (INSERT a Neon con event ids)."""

from __future__ import annotations

from typing import Any

import pytest

from stream_processor import pg_writer

pytestmark = pytest.mark.unit


class _FakeCursor:
    """Cursor fake que captura el SQL y los params del ultimo execute()."""

    def __init__(self) -> None:
        self.sql: str = ''
        self.params: Any = None
        self.fetch_result: Any = None
        self.executed: list[tuple[str, Any]] = []

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, sql: str, params: Any = None) -> None:
        self.sql = sql
        self.params = params
        self.executed.append((sql, params))

    def fetchone(self) -> Any:
        return self.fetch_result


class _FakeConnection:
    """Conexion fake: entrega siempre el mismo _FakeCursor."""

    def __init__(self) -> None:
        self.cursor_obj = _FakeCursor()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self) -> _FakeCursor:
        return self.cursor_obj

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class TestGetConnection:
    """_get_connection - lazy connection cacheada entre invocaciones warm."""

    def test_when_no_connection_then_connects_once_and_caches(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given el singleton _conn sin inicializar,
        When _get_connection se invoca dos veces,
        Then psycopg.connect se llama una sola vez (la 2a reusa el cache).
        """
        import psycopg

        monkeypatch.setattr(pg_writer, '_conn', None)

        calls: list[str] = []

        def _fake_connect(db_url: str, **_kw: Any) -> _FakeConnection:
            calls.append(db_url)
            return _FakeConnection()

        monkeypatch.setattr(psycopg, 'connect', _fake_connect)
        monkeypatch.setattr(
            'common.ssm_client.get_secret', lambda _path: 'postgres://x'
        )

        first = pg_writer._get_connection()
        second = pg_writer._get_connection()

        assert first is second
        assert calls == ['postgres://x']


def _tracking_payload(**overrides: Any) -> dict[str, Any]:
    """Payload de tracking minimo para upsert_tracking, con overrides."""
    payload: dict[str, Any] = {
        'session_id': 'sess-3',
        'page_id': 'page-uuid-3',
        'stream_event_id': 'evt-200',
        'created_at': '2026-05-17T00:00:00Z',
        'expires_at': 1750000000,
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


class TestUpsertTracking:
    """upsert_tracking - el INSERT incluye event_id, event_type_id, props."""

    def test_when_payload_has_event_ids_then_insert_includes_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload de tracking con event_id y event_type_id [AC-7],
        When upsert_tracking arma el INSERT,
        Then la sentencia nombra ambas columnas y los params se pasan.
        """
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        payload = _tracking_payload()

        pg_writer.upsert_tracking(payload)

        sql = fake_conn.cursor_obj.sql
        params = fake_conn.cursor_obj.params
        assert 'event_id' in sql
        assert 'event_type_id' in sql
        assert '%(event_id)s' in sql
        assert '%(event_type_id)s' in sql
        assert params['event_id'] == 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
        assert params['event_type_id'] == (
            '019e372b-e0a7-7154-8279-8829bcf6a08c'
        )

    def test_when_payload_has_event_props_then_insert_includes_column(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload de tracking con event_props (dict de contexto) [AC-10],
        When upsert_tracking arma el INSERT,
        Then la sentencia nombra la columna event_props con su placeholder.
        """
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        pg_writer.upsert_tracking(
            _tracking_payload(event_props={'href': 'https://x.com'})
        )

        sql = fake_conn.cursor_obj.sql
        assert 'event_props' in sql
        assert '%(event_props)s' in sql

    def test_when_event_props_present_then_param_wrapped_as_jsonb(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given event_props como dict en el payload [AC-10],
        When upsert_tracking adapta los params,
        Then event_props viaja envuelto en psycopg Jsonb (adaptacion jsonb).
        """
        from psycopg.types.json import Jsonb

        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)
        props = {'depth': 50, 'href': 'https://x.com'}

        pg_writer.upsert_tracking(_tracking_payload(event_props=props))

        param = fake_conn.cursor_obj.params['event_props']
        assert isinstance(param, Jsonb)
        assert param.obj == props

    def test_when_event_props_none_then_param_stays_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload sin event_props (None) [AC-10],
        When upsert_tracking adapta los params,
        Then event_props se pasa como None (columna jsonb nullable).
        """
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        pg_writer.upsert_tracking(_tracking_payload(event_props=None))

        assert fake_conn.cursor_obj.params['event_props'] is None


class TestUpsertContact:
    """upsert_contact - INSERT idempotente en contacts."""

    def test_when_called_then_insert_has_on_conflict_do_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload de contacto,
        When upsert_contact arma el INSERT,
        Then la sentencia usa ON CONFLICT (id) DO NOTHING (idempotencia).
        """
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        pg_writer.upsert_contact({'id': 'contact-uuid'})

        assert 'ON CONFLICT (id) DO NOTHING' in fake_conn.cursor_obj.sql

    def test_when_payload_has_session_id_then_insert_includes_column(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload de contacto con session_id [AC-6],
        When upsert_contact arma el INSERT,
        Then la sentencia nombra la columna session_id y su placeholder.
        """
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        pg_writer.upsert_contact({
            'id': 'contact-uuid',
            'session_id': 'a' * 32,
        })

        sql = fake_conn.cursor_obj.sql
        assert 'session_id' in sql
        assert '%(session_id)s' in sql

    def test_when_legacy_fields_null_then_insert_keeps_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload de contacto con ip/country/user_agent en NULL [AC-6],
        When upsert_contact arma el INSERT,
        Then las columnas legacy siguen en la sentencia (no se eliminan) y
        los params se pasan con valor None.
        """
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        payload = {
            'id': 'contact-uuid',
            'stream_event_id': 'evt-1',
            'created_at': '2026-05-17T00:00:00Z',
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

        pg_writer.upsert_contact(payload)

        sql = fake_conn.cursor_obj.sql
        assert 'ip' in sql
        assert 'country' in sql
        assert 'user_agent' in sql
        assert fake_conn.cursor_obj.params == payload


class TestIdempotencyLog:
    """is_event_processed + mark_event_processed - log de idempotencia."""

    def test_when_event_in_log_then_is_processed_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un event_id ya registrado en processed_stream_events [AC-5],
        When is_event_processed lo consulta,
        Then retorna True (el handler lo saltea, no duplica la fila).
        """
        fake_conn = _FakeConnection()
        fake_conn.cursor_obj.fetch_result = (1,)
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        assert pg_writer.is_event_processed('evt-already-done') is True

    def test_when_event_not_in_log_then_is_processed_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un event_id que no esta en processed_stream_events [AC-5],
        When is_event_processed lo consulta,
        Then retorna False.
        """
        fake_conn = _FakeConnection()
        fake_conn.cursor_obj.fetch_result = None
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        assert pg_writer.is_event_processed('evt-new') is False

    def test_when_mark_processed_then_insert_on_conflict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un event_id procesado,
        When mark_event_processed lo registra,
        Then el INSERT usa ON CONFLICT DO NOTHING.
        """
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        pg_writer.mark_event_processed(
            'evt-1', event_type='INSERT', table_name='tracking'
        )

        assert 'ON CONFLICT (event_id) DO NOTHING' in fake_conn.cursor_obj.sql


class TestTransactionControl:
    """commit / rollback - control de transaccion."""

    def test_when_commit_then_connection_commits(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given una conexion abierta, When commit(), Then conn.commit()."""
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        pg_writer.commit()

        assert fake_conn.committed is True

    def test_when_rollback_then_connection_rolls_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given una conexion abierta, When rollback(), Then conn.rollback()."""
        fake_conn = _FakeConnection()
        monkeypatch.setattr(pg_writer, '_get_connection', lambda: fake_conn)

        pg_writer.rollback()

        assert fake_conn.rolled_back is True
