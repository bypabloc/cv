"""
Given DATABASE_URL apuntando a una SQLite in-memory,
When get_engine se invoca dos veces y se usa db_session para un SELECT,
Then el engine se reusa (lru_cache module-scope) y la sesion ejecuta SQL.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def test_session_engine_reuse_e2e(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_engine cachea el engine; db_session ejecuta un SELECT real."""
    # Arrange: SQLite in-memory evita depender de Neon real.
    monkeypatch.setenv('DATABASE_URL', 'sqlite://')
    # Limpiar los lru_cache module-scope para aislar el test.
    from shared.db.session import (
        _session_factory,
        db_session,
        get_engine,
    )

    get_engine.cache_clear()
    _session_factory.cache_clear()

    # Act
    engine_a = get_engine()
    engine_b = get_engine()
    with db_session() as session:
        value = session.execute(text('SELECT 42')).scalar_one()

    # Assert
    assert engine_a is engine_b
    assert value == 42

    # Cleanup: no dejar el engine SQLite cacheado para otros tests.
    get_engine.cache_clear()
    _session_factory.cache_clear()
