"""shared.lambda_kit.base_controller.BaseController.preload.

Given un controller con arn_config_key apuntando a un campo ausente en
     el AppConfig inyectado,
When se ejecuta preload,
Then devuelve {is_valid: False} con error_code CONFIGURATION_MISSING.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import shared.lambda_kit.base_controller as bc
from shared.lambda_kit.error_codes import ErrorCode

pytestmark = pytest.mark.unit


def test_base_controller_preload_fails_when_arn_missing(
    make_controller,
) -> None:
    # Arrange
    bc.set_app_config(SimpleNamespace())
    controller = make_controller(arn_config_key='missing_arn')(event={})

    # Act
    result = controller.preload()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'CONFIGURATION_MISSING',
            'message': 'MISSING_ARN no configurado',
        },
        'code': ErrorCode.CONFIGURATION_MISSING.value,
    }
