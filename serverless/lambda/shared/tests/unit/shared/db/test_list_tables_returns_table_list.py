"""shared.db.repository.list_tables.

Given una DB con tablas de usuario,
When se invoca list_tables,
Then devuelve la lista de tablas con el estimado de filas, ordenada
     descendente por filas.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from shared.db.repository import list_tables

pytestmark = pytest.mark.unit


def test_list_tables_returns_table_list() -> None:
    # Arrange
    rows = [
        SimpleNamespace(table_name='public.contacts', estimated_rows=42),
        SimpleNamespace(table_name='public.tracking', estimated_rows=7),
    ]
    conn = MagicMock()
    conn.execute.return_value.all.return_value = rows
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn

    # Act
    with patch('shared.db.repository.get_engine', return_value=engine):
        result = list_tables()

    # Assert
    assert result == {
        'tables': [
            {'name': 'public.contacts', 'rows': 42},
            {'name': 'public.tracking', 'rows': 7},
        ],
    }
