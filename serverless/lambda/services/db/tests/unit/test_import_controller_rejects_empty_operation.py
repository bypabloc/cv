"""Util import_controller.import_controller — operation vacia.

Given una operation vacia,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code INVALID_OPERATION.
"""

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_import_controller_rejects_empty_operation():
    from utils.import_controller import import_controller

    # Act
    result = import_controller('', 'migrate')

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'INVALID_OPERATION',
            'message': 'Operation name cannot be empty',
        },
        'code': ErrorCode.VALIDATION_ERROR.value,
        'class': None,
    }
