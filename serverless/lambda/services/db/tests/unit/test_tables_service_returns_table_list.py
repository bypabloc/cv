"""Service db_service.run_tables.

Given una DB con tablas de usuario,
When se invoca run_tables,
Then consulta pg_stat_user_tables y devuelve cada tabla con su estimado
     de filas, ordenado segun lo que devuelve la query.
"""

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def test_tables_service_returns_table_list():
    from services.db_service import run_tables

    # Arrange
    rows = [
        SimpleNamespace(table_name='public.tracking_events',
                        estimated_rows=15000),
        SimpleNamespace(table_name='public.contacts', estimated_rows=200),
    ]
    mock_conn = MagicMock()
    mock_conn.execute.return_value.all.return_value = rows
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    with (
        patch.dict(os.environ, {'DATABASE_URL': 'postgresql://x/y'}),
        patch(
            'sqlalchemy.create_engine', return_value=mock_engine
        ) as mock_create,
    ):
        # Act
        result = run_tables()

    # Assert
    assert mock_create.call_count == 1
    assert result == {
        'tables': [
            {'name': 'public.tracking_events', 'rows': 15000},
            {'name': 'public.contacts', 'rows': 200},
        ],
    }
