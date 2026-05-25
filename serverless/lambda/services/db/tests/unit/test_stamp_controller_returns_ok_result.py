"""Controller db/stamp.

Given el service run_stamp exitoso,
When el controller Stamp ejecuta su ciclo run(),
Then devuelve {is_valid: True, code: 0} con el resultado normalizado.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_stamp_controller_returns_ok_result():
    from controllers.db.stamp import Stamp

    # Arrange
    with patch(
        'controllers.db.stamp.run_stamp',
        return_value={'target': 'head', 'current': '81c2cc51db34'},
    ):
        controller = Stamp(event={'target': 'head'})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': True,
        'code': 0,
        'data': {
            'command': 'stamp',
            'status': 'ok',
            'target': 'head',
            'current': '81c2cc51db34',
        },
    }
