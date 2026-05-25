"""shared.lambda_kit.import_controller.import_controller.

Given una action vacia,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code INVALID_ACTION.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.error_codes import ErrorCode
from shared.lambda_kit.import_controller import import_controller

pytestmark = pytest.mark.unit


def test_import_controller_rejects_empty_action() -> None:
    # Act
    result = import_controller('contact', '', {})

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
