"""shared.lambda_kit.base_controller.BaseController.run (fase Authorize).

Given un controller con required_permission='admin' y SIN checker
     inyectado (set_permission_checker nunca llamado),
When se ejecuta run,
Then devuelve CONFIGURATION_MISSING (2001) y execute NO se ejecuta.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.error_codes import ErrorCode

pytestmark = pytest.mark.unit


def test_base_controller_authorize_missing_checker_fails(
    make_controller,
) -> None:
    # Arrange
    controller = make_controller(
        execute_result={'is_valid': True, 'data': {'ran': True}, 'code': 0},
        required_permission='admin',
    )(event={})

    # Act
    result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'CONFIGURATION_MISSING',
            'message': 'permission checker no configurado',
        },
        'code': ErrorCode.CONFIGURATION_MISSING.value,
    }
