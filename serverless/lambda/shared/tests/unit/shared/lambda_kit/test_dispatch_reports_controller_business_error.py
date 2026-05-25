"""shared.lambda_kit.dispatch.run_controller.

Given un controller que resuelve pero su execute devuelve is_valid=False,
When se invoca run_controller,
Then devuelve un DispatchResult con stage='controller' e is_valid=False.
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
    """Controller sintetico que devuelve un error de negocio."""

    def execute(self) -> dict:
        return {
            'is_valid': False,
            'data': {'error_code': 'RATE_LIMITED'},
            'code': 4001,
        }


def test_dispatch_reports_controller_business_error() -> None:
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
    assert result.is_valid is False
    assert result.code == 4001
    assert result.data == {'error_code': 'RATE_LIMITED'}
