"""Controller db/tables.

Given el service run_tables exitoso,
When el controller Tables ejecuta su ciclo run(),
Then devuelve {is_valid: True, code: 0} con el resultado normalizado.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_tables_controller_returns_ok_result():
    from controllers.db.tables import Tables

    # Arrange
    with patch(
        'controllers.db.tables.run_tables',
        return_value={'tables': [{'name': 'public.contacts', 'rows': 200}]},
    ):
        controller = Tables(event={})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': True,
        'code': 0,
        'data': {
            'command': 'tables',
            'status': 'ok',
            'tables': [{'name': 'public.contacts', 'rows': 200}],
        },
    }
