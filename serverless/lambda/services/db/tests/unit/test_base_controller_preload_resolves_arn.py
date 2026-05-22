"""Util base_controller.BaseController.preload — ARN downstream.

Given un controller con arn_config_key apuntando a un campo de app_config
     que tiene un valor,
When se ejecuta preload,
Then resuelve el ARN en self.arn y devuelve {is_valid: True}.
"""

import pytest

pytestmark = pytest.mark.unit


def test_base_controller_preload_resolves_arn():
    from settings.config import app_config
    from utils.base_controller import BaseController

    class _WithArn(BaseController):
        arn_config_key = 'environment'  # campo existente de AppConfig

        def execute(self) -> dict:
            return {'is_valid': True, 'data': {}, 'code': 0}

    # Arrange
    controller = _WithArn(event={})

    # Act
    result = controller.preload()

    # Assert
    assert result == {'is_valid': True, 'data': {}, 'code': 0}
    assert controller.arn == app_config.environment
