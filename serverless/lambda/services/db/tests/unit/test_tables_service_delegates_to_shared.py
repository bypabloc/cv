"""Service db_service.run_tables.

Given una DB con tablas,
When se invoca run_tables,
Then delega en shared.db.repository.list_tables y devuelve su resultado.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_tables_service_delegates_to_shared():
    from services.db_service import run_tables

    # Arrange
    expected = {'tables': [{'name': 'public.contacts', 'rows': 5}]}
    with patch(
        'services.db_service._shared_list_tables',
        return_value=expected,
    ) as mock_shared:
        # Act
        result = run_tables()

    # Assert
    assert result == expected
    assert mock_shared.call_count == 1
