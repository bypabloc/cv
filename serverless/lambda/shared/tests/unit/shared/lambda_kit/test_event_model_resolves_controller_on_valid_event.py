"""shared.lambda_kit.event_model.build_event_model.

Given un evento bien formado y un OPERATIONS cuyo controller resuelve,
When EventModel.validate_event lo procesa,
Then devuelve una instancia con el controller resuelto y los datos
     preparados.
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


def test_event_model_resolves_controller_on_valid_event() -> None:
    # Arrange
    operations = {'demo': {'controller': 'demo', 'arn_key': ''}}
    event_model = build_event_model(operations)
    fake_module = ModuleType('controllers.demo.create')
    fake_module.Create = _Create
    event = {
        'operation': 'demo',
        'action': 'create',
        'data': {'name': 'pablo'},
    }

    # Act
    with patch(
        'shared.lambda_kit.import_controller.import_module',
        return_value=fake_module,
    ):
        validated = event_model.validate_event(event)

    # Assert
    assert validated.operation == 'demo'
    assert validated.action == 'create'
    assert validated.controller_event == {'name': 'pablo'}
    assert (
        validated.controller_info['data']['controller_class'] is _Create
    )
