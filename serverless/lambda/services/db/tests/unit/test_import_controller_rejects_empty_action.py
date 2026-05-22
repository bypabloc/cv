"""Util import_controller.import_controller — action vacia.

Given una operation valida pero una action vacia,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code INVALID_ACTION.
"""

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_import_controller_rejects_empty_action():
    from utils.import_controller import import_controller

    # Act
    result = import_controller('db', '')

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'INVALID_ACTION',
            'message': 'Action name cannot be empty',
        },
        'code': ErrorCode.VALIDATION_ERROR.value,
        'class': None,
    }
