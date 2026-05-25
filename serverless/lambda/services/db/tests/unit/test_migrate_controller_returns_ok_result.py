"""Controller db/migrate.

Given el service run_migrate exitoso,
When el controller Migrate ejecuta su ciclo run(),
Then devuelve {is_valid: True, code: 0} con el resultado normalizado.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_migrate_controller_returns_ok_result():
    from controllers.db.migrate import Migrate

    # Arrange
    with patch(
        'controllers.db.migrate.run_migrate',
        return_value={'target': 'head', 'current': '81c2cc51db34'},
    ):
        controller = Migrate(event={'target': 'head'})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': True,
        'code': 0,
        'data': {
            'command': 'migrate',
            'status': 'ok',
            'target': 'head',
            'current': '81c2cc51db34',
        },
    }
