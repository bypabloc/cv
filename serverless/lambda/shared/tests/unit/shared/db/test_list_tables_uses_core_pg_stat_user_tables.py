"""shared.db.repository.list_tables — guardia SQL Core.

Given una DB de prueba,
When list_tables construye el statement,
Then compila a un SELECT contra `pg_stat_user_tables` ordenado DESC
     por n_live_tup, sin raw SQL.

Guardia del cleanup de raw SQL: antes la query era un str inmutable
(`_TABLES_QUERY`). Ahora es un `select()` de SQLAlchemy Core sobre
una Table del catalogo de Postgres.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from shared.db import repository
from shared.db.repository import list_tables
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import Select

pytestmark = pytest.mark.unit


def test_list_tables_executes_core_select_against_pg_stat_user_tables() -> None:
    # Arrange
    rows = [
        SimpleNamespace(table_name='public.cv_persons', estimated_rows=100),
        SimpleNamespace(
            table_name='public.vis_session_visits', estimated_rows=42
        ),
    ]
    conn = MagicMock()
    conn.execute.return_value.all.return_value = rows
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn

    # Act
    with patch('shared.db.repository.get_engine', return_value=engine):
        result = list_tables()

    # Assert — resultado correcto
    assert result == {
        'tables': [
            {'name': 'public.cv_persons', 'rows': 100},
            {'name': 'public.vis_session_visits', 'rows': 42},
        ],
    }

    # Assert — el argumento de conn.execute es un Core Select (no text)
    assert conn.execute.call_count == 1
    stmt = conn.execute.call_args[0][0]
    assert isinstance(stmt, Select), f'esperaba Select, recibi {type(stmt)}'
    compiled = str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={'literal_binds': True},
        )
    )
    assert 'FROM pg_stat_user_tables' in compiled
    assert 'ORDER BY pg_stat_user_tables.n_live_tup DESC' in compiled
    # Guardia: el modulo expone la Table como _pg_stat_user_tables
    assert repository._pg_stat_user_tables.name == 'pg_stat_user_tables'
    cols = {c.name for c in repository._pg_stat_user_tables.c}
    assert cols == {'schemaname', 'relname', 'n_live_tup'}
