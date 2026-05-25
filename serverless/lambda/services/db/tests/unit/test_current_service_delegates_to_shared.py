"""Service db_service.run_current.

Given una DB con una revision aplicada,
When se invoca run_current,
Then delega en shared.db.migrations.run_current y devuelve su resultado.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_current_service_delegates_to_shared():
    from services.db_service import run_current

    # Arrange
    expected = {'current': 'rev1'}
    with patch(
        'services.db_service._shared_run_current',
        return_value=expected,
    ) as mock_shared:
        # Act
        result = run_current()

    # Assert
    assert result == expected
    assert mock_shared.call_count == 1
