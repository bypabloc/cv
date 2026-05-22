"""Modelo event.EventModel.validate_event — controller_result sin 'data'.

Given import_controller que devuelve un resultado valido pero sin la
     clave 'data',
When se invoca EventModel.validate_event,
Then construye el EventModel igual, sin intentar inyectar operation/action
     en el dict 'data' (rama 'data' not in controller_result).
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_event_model_builds_when_controller_result_lacks_data():
    from models.event import EventModel

    # Arrange: resultado valido pero sin la clave 'data'.
    fake_result = {'is_valid': True, 'code': 0, 'class': object()}
    event = {'operation': 'db', 'action': 'current', 'data': {}}

    with patch('models.event.import_controller', return_value=fake_result):
        # Act
        model = EventModel.validate_event(event)

    # Assert
    assert model.operation == 'db'
    assert model.action == 'current'
    assert model.controller_info == fake_result
