"""Util import_controller.import_controller — modulo inexistente.

Given una operation valida y una action cuyo modulo controller no existe,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code MODULE_NOT_FOUND.
"""

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_import_controller_reports_module_not_found():
    from utils.import_controller import import_controller

    # Act: no existe controllers/db/nonexistent.py
    result = import_controller('db', 'nonexistent')

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'MODULE_NOT_FOUND',
            'message': (
                "Controller module 'controllers.db.nonexistent' not found"
            ),
        },
        'code': ErrorCode.VALIDATION_ERROR.value,
        'class': None,
    }
