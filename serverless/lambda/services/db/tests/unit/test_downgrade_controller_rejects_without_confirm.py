"""Controller db/downgrade.

Given un payload sin 'confirm: true',
When el controller Downgrade ejecuta su ciclo run(),
Then rechaza con code DOWNGRADE_NOT_CONFIRMED y NO invoca el service.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_downgrade_controller_rejects_without_confirm():
    from controllers.db.downgrade import Downgrade
    from settings.config import ErrorCode

    # Arrange
    with patch(
        'controllers.db.downgrade.run_downgrade',
    ) as mock_run:
        controller = Downgrade(event={'target': '-1', 'confirm': False})

        # Act
        result = controller.run()

    # Assert
    assert result['is_valid'] is False
    assert result['code'] == ErrorCode.DOWNGRADE_NOT_CONFIRMED.value
    assert mock_run.call_count == 0
