"""Modelo event.EventModel.validate_event — action no string.

Given un evento cuya 'action' no es un string,
When se invoca EventModel.validate_event,
Then lanza un ValueError indicando que la accion no es valida.
"""

import pytest

pytestmark = pytest.mark.unit


def test_event_model_rejects_non_string_action():
    from models.event import EventModel

    # Act + Assert
    with pytest.raises(ValueError) as exc_info:
        EventModel.validate_event({'operation': 'db', 'action': 42, 'data': {}})

    assert str(exc_info.value) == 'La accion 42 no es valida'
