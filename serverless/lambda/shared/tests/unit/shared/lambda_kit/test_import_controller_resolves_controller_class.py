"""shared.lambda_kit.import_controller.import_controller.

Given una operation/action cuyo modulo expone una clase que hereda de
     BaseController,
When se invoca import_controller,
Then devuelve {is_valid: True} con esa clase resuelta.
"""

from __future__ import annotations

from types import ModuleType
from unittest.mock import patch

import pytest
from shared.lambda_kit.base_controller import BaseController
from shared.lambda_kit.import_controller import import_controller

pytestmark = pytest.mark.unit


class _Create(BaseController):
    """Controller sintetico valido."""

    def execute(self) -> dict:
        return {'is_valid': True, 'data': {}, 'code': 0}


def test_import_controller_resolves_controller_class() -> None:
    # Arrange
    operations = {'demo': {'controller': 'demo', 'arn_key': ''}}
    fake_module = ModuleType('controllers.demo.create')
    fake_module.Create = _Create

    # Act
    with patch(
        'shared.lambda_kit.import_controller.import_module',
        return_value=fake_module,
    ):
        result = import_controller('demo', 'create', operations)

    # Assert
    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['class'] is _Create
    assert result['data']['controller_class'] is _Create
    assert result['data']['class_name'] == 'Create'
