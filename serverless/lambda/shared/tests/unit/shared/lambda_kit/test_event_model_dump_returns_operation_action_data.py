"""shared.lambda_kit.event_model.build_event_model.

Given una instancia EventModel resuelta,
When se invoca model_dump,
Then devuelve un dict con operation, action y data.
"""

from __future__ import annotations

from types import ModuleType
from unittest.mock import patch

import pytest
from shared.lambda_kit.base_controller import BaseController
from shared.lambda_kit.event_model import build_event_model

pytestmark = pytest.mark.unit


class _Create(BaseController):
    """Controller sintetico valido."""

    def execute(self) -> dict:
        return {'is_valid': True, 'data': {}, 'code': 0}


def test_event_model_dump_returns_operation_action_data() -> None:
    # Arrange
    operations = {'demo': {'controller': 'demo', 'arn_key': ''}}
    event_model = build_event_model(operations)
    fake_module = ModuleType('controllers.demo.create')
    fake_module.Create = _Create
    event = {'operation': 'demo', 'action': 'create', 'data': {'n': 1}}

    # Act
    with patch(
        'shared.lambda_kit.import_controller.import_module',
        return_value=fake_module,
    ):
        validated = event_model.validate_event(event)
        dumped = validated.model_dump()

    # Assert
    assert dumped == {
        'operation': 'demo',
        'action': 'create',
        'data': {'n': 1},
    }
