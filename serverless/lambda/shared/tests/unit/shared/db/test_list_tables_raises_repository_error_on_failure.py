"""shared.db.repository.list_tables.

Given una DB inaccesible (la query falla),
When se invoca list_tables,
Then lanza RepositoryError con code 5000 y error_code DB_QUERY_FAILED.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.db.repository import RepositoryError, list_tables

pytestmark = pytest.mark.unit


def test_list_tables_raises_repository_error_on_failure() -> None:
    # Arrange
    def boom() -> None:
        raise RuntimeError('connection refused')

    # Act
    with (
        patch('shared.db.repository.get_engine', side_effect=boom),
        pytest.raises(RepositoryError) as exc_info,
    ):
        list_tables()

    # Assert
    assert exc_info.value.code == 5000
    assert exc_info.value.error_code == 'DB_QUERY_FAILED'
