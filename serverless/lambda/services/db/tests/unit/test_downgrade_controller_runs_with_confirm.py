"""Controller db/downgrade.

Given un payload con 'confirm: true' y un target,
When el controller Downgrade ejecuta su ciclo run(),
Then invoca el service y devuelve {is_valid: True, code: 0}.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_downgrade_controller_runs_with_confirm():
    from controllers.db.downgrade import Downgrade

    # Arrange
    with patch(
        'controllers.db.downgrade.run_downgrade',
        return_value={'target': '-1', 'current': 'rev1'},
    ) as mock_run:
        controller = Downgrade(event={'target': '-1', 'confirm': True})

        # Act
        result = controller.run()

    # Assert
    assert mock_run.call_count == 1
    assert result == {
        'is_valid': True,
        'code': 0,
        'data': {
            'command': 'downgrade',
            'status': 'ok',
            'target': '-1',
            'current': 'rev1',
        },
    }
