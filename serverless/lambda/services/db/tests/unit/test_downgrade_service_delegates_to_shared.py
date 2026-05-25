"""Service db_service.run_downgrade.

Given un target de downgrade,
When se invoca run_downgrade,
Then delega en shared.db.migrations.run_downgrade con ese target.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_downgrade_service_delegates_to_shared():
    from services.db_service import run_downgrade

    # Arrange
    expected = {'target': '-1', 'current': 'base'}
    with patch(
        'services.db_service._shared_run_downgrade',
        return_value=expected,
    ) as mock_shared:
        # Act
        result = run_downgrade(target='-1')

    # Assert
    assert result == expected
    assert mock_shared.call_args.kwargs == {'target': '-1'}
