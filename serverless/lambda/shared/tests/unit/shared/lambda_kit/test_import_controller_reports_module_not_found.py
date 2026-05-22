"""shared.lambda_kit.import_controller.import_controller.

Given una operation/action cuyo modulo controller no existe,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code MODULE_NOT_FOUND.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.error_codes import ErrorCode
from shared.lambda_kit.import_controller import import_controller

pytestmark = pytest.mark.unit


def test_import_controller_reports_module_not_found() -> None:
    # Arrange: el codename 'demo' resuelve al controller 'demo'
    operations = {'demo': {'controller': 'demo', 'arn_key': ''}}

    # Act: no existe controllers/demo/nonexistent.py
    result = import_controller('demo', 'nonexistent', operations)

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'MODULE_NOT_FOUND',
            'message': (
                "Controller module 'controllers.demo.nonexistent' "
                'not found'
            ),
        },
        'code': ErrorCode.VALIDATION_ERROR.value,
        'class': None,
    }
