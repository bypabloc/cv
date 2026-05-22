"""Util import_controller.import_controller — clase ausente en el modulo.

Given un modulo controller que existe pero no expone la clase
     action.capitalize(),
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code CLASS_NOT_FOUND.
"""

import types
from unittest.mock import patch

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_import_controller_reports_class_not_found():
    from utils.import_controller import import_controller

    # Arrange: modulo sin la clase 'Migrate'.
    empty_module = types.ModuleType('controllers.db.migrate')
    with patch(
        'utils.import_controller.import_module', return_value=empty_module
    ):
        # Act
        result = import_controller('db', 'migrate')

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'CLASS_NOT_FOUND',
            'message': (
                "Controller class 'Migrate' not found in module "
                "'controllers.db.migrate'"
            ),
        },
        'code': ErrorCode.VALIDATION_ERROR.value,
        'class': None,
    }
