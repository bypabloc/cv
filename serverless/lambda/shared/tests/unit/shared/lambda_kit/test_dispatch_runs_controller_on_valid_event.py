"""shared.lambda_kit.dispatch.run_controller.

Given un evento sintetico bien formado cuyo controller resuelve y
     ejecuta con exito,
When se invoca run_controller,
Then devuelve un DispatchResult con stage='controller', is_valid=True y
     el data del controller.
"""

from __future__ import annotations

from types import ModuleType
from unittest.mock import patch

import pytest
from shared.lambda_kit.base_controller import BaseController
from shared.lambda_kit.dispatch import run_controller
from shared.lambda_kit.event_model import build_event_model

pytestmark = pytest.mark.unit


class _Create(BaseController):
    """Controller sintetico que devuelve un resultado de exito."""

    def execute(self) -> dict:
        return {'is_valid': True, 'data': {'id': 'x-1'}, 'code': 0}


def test_dispatch_runs_controller_on_valid_event() -> None:
    # Arrange
    operations = {'demo': {'controller': 'demo', 'arn_key': ''}}
    event_model = build_event_model(operations)
    fake_module = ModuleType('controllers.demo.create')
    fake_module.Create = _Create
    event = {'operation': 'demo', 'action': 'create', 'data': {}}

    # Act
    with patch(
        'shared.lambda_kit.import_controller.import_module',
        return_value=fake_module,
    ):
        result = run_controller(event, event_model)

    # Assert
    assert result.stage == 'controller'
    assert result.is_valid is True
    assert result.code == 0
    assert result.data == {'id': 'x-1'}
