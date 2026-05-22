"""Util base_controller.BaseController — preload con ARN ausente.

Given un controller con arn_config_key que apunta a un campo inexistente
     de app_config,
When se ejecuta el ciclo run(),
Then preload devuelve {is_valid: False} con CONFIGURATION_MISSING y run()
     corta sin llegar a execute.
"""

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_base_controller_preload_fails_when_arn_missing():
    from utils.base_controller import BaseController

    class _MissingArn(BaseController):
        arn_config_key = 'nonexistent_arn_field'

        def execute(self) -> dict:
            raise AssertionError('execute no debe ejecutarse')

    # Arrange
    controller = _MissingArn(event={})

    # Act
    result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'CONFIGURATION_MISSING',
            'message': 'NONEXISTENT_ARN_FIELD no configurado',
        },
        'code': ErrorCode.CONFIGURATION_MISSING.value,
    }
