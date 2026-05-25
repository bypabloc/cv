"""Controller db/seed.

Given el service run_seed que puebla la DB y devuelve conteos,
When el controller Seed ejecuta su ciclo run(),
Then devuelve {is_valid: True, code: 0} con el resultado normalizado.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_seed_controller_returns_ok_result():
    from controllers.db.seed import Seed

    # Arrange
    with patch(
        'controllers.db.seed.run_seed',
        return_value={
            'seeded': True,
            'counts': {'profile': 1, 'experiences': 9},
        },
    ):
        controller = Seed(event={})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': True,
        'code': 0,
        'data': {
            'command': 'seed',
            'status': 'ok',
            'seeded': True,
            'counts': {'profile': 1, 'experiences': 9},
        },
    }
