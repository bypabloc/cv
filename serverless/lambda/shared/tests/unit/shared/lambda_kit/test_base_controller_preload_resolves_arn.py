"""shared.lambda_kit.base_controller.BaseController.preload.

Given un controller con arn_config_key y un AppConfig inyectado que
     tiene ese campo con valor,
When se ejecuta preload,
Then resuelve el ARN en self.arn y devuelve {is_valid: True}.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from shared.lambda_kit import base_controller as bc

pytestmark = pytest.mark.unit


def test_base_controller_preload_resolves_arn(make_controller) -> None:
    # Arrange
    bc.set_app_config(SimpleNamespace(downstream_arn='arn:aws:lambda:x'))
    controller = make_controller(arn_config_key='downstream_arn')(event={})

    # Act
    result = controller.preload()

    # Assert
    assert result == {'is_valid': True, 'data': {}, 'code': 0}
    assert controller.arn == 'arn:aws:lambda:x'
