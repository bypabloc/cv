"""Modelo event.EventModel.validate_event — sin action.

Given un evento sin la clave 'action',
When se invoca EventModel.validate_event,
Then lanza un ValueError indicando que la accion None no es valida.
"""

import pytest

pytestmark = pytest.mark.unit


def test_event_model_rejects_missing_action():
    from models.event import EventModel

    # Act + Assert
    with pytest.raises(ValueError) as exc_info:
        EventModel.validate_event({'operation': 'db', 'data': {}})

    assert str(exc_info.value) == 'La accion None no es valida'
