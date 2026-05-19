"""Unit tests para _shared.db.session (engine + db_session context manager)."""

from __future__ import annotations

from typing import Any

import pytest

from _shared.db import session as session_mod

pytestmark = pytest.mark.unit


def _clear_lru_caches() -> None:
    """Limpia los lru_cache de engine/factory si aun los tienen.

    Un test puede sustituir `_session_factory` por una funcion plana via
    monkeypatch; `getattr(..., 'cache_clear', None)` evita romper en ese caso.
    """
    for fn in (session_mod.get_engine, session_mod._session_factory):
        clear = getattr(fn, 'cache_clear', None)
        if clear is not None:
            clear()


@pytest.fixture(autouse=True)
def _clear_caches() -> Any:
    """Limpia los lru_cache de engine/factory entre tests (estado global)."""
    _clear_lru_caches()
    yield
    _clear_lru_caches()


class _FakeSession:
    """Session fake: cuenta commit / rollback / close."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class TestGetEngine:
    """get_engine - engine cacheado a module-scope."""

    def test_when_called_twice_then_engine_created_once(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given get_engine invocado dos veces,
        When,
        Then create_engine se llama una sola vez (lru_cache devuelve la
        misma instancia).
        """
        calls: list[str] = []

        def _fake_create_engine(urlarg: str, **_kw: Any) -> object:
            calls.append(urlarg)
            return object()

        monkeypatch.setattr(
            '_shared.db.session.resolve_database_url',
            lambda: 'postgresql+psycopg://u:p@h/db',
        )
        monkeypatch.setattr(
            session_mod, 'create_engine', _fake_create_engine
        )

        first = session_mod.get_engine()
        second = session_mod.get_engine()

        assert first is second
        assert calls == ['postgresql+psycopg://u:p@h/db']


class TestDbSession:
    """db_session - context manager: commit / rollback / close."""

    def _wire_factory(
        self, monkeypatch: pytest.MonkeyPatch, fake: _FakeSession
    ) -> None:
        """Sustituye el sessionmaker para que entregue la Session fake."""
        monkeypatch.setattr(
            session_mod, '_session_factory', lambda: (lambda: fake)
        )

    def test_when_block_exits_clean_then_commits_and_closes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un bloque `with db_session()` que termina sin excepcion,
        When sale del context manager,
        Then la Session hace commit y close (sin rollback).
        """
        fake = _FakeSession()
        self._wire_factory(monkeypatch, fake)

        with session_mod.db_session() as sess:
            assert sess is fake

        assert fake.committed is True
        assert fake.rolled_back is False
        assert fake.closed is True

    def test_when_block_raises_then_rolls_back_and_closes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un bloque `with db_session()` que lanza una excepcion,
        When sale del context manager,
        Then la Session hace rollback y close (sin commit), y la excepcion
        se re-propaga.
        """
        fake = _FakeSession()
        self._wire_factory(monkeypatch, fake)

        with (
            pytest.raises(ValueError, match='boom'),
            session_mod.db_session(),
        ):
            raise ValueError('boom')

        assert fake.committed is False
        assert fake.rolled_back is True
        assert fake.closed is True
