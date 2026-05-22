"""Util import_controller.import_controller — clase no BaseController.

Given un modulo controller cuya clase action.capitalize() existe pero NO
     hereda de BaseController,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code INVALID_CONTROLLER.
"""

import types
from unittest.mock import patch

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_import_controller_rejects_non_base_controller_class():
    from utils.import_controller import import_controller

    # Arrange: modulo con una clase 'Migrate' que no es BaseController.
    fake_module = types.ModuleType('controllers.db.migrate')

    class Migrate:
        pass

    fake_module.Migrate = Migrate

    with patch(
        'utils.import_controller.import_module', return_value=fake_module
    ):
        # Act
        result = import_controller('db', 'migrate')

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'INVALID_CONTROLLER',
            'message': (
                "Controller 'Migrate' in 'controllers.db.migrate' "
                'must inherit from BaseController'
            ),
        },
        'code': ErrorCode.VALIDATION_ERROR.value,
        'class': None,
    }
