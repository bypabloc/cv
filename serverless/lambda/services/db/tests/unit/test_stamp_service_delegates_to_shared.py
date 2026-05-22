"""Service db_service.run_stamp.

Given un target a marcar,
When se invoca run_stamp,
Then delega en shared.db.migrations.run_stamp con ese target.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_stamp_service_delegates_to_shared():
    from services.db_service import run_stamp

    # Arrange
    expected = {'target': 'head', 'current': 'rev1'}
    with patch(
        'services.db_service._shared_run_stamp',
        return_value=expected,
    ) as mock_shared:
        # Act
        result = run_stamp(target='head')

    # Assert
    assert result == expected
    assert mock_shared.call_args.kwargs == {'target': 'head'}
