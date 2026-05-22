"""Modelo event.EventModel.validate_event — data no es dict.

Given un evento cuyo 'data' no es un objeto JSON,
When se invoca EventModel.validate_event,
Then lanza un ValueError indicando que data debe ser un objeto.
"""

import pytest

pytestmark = pytest.mark.unit


def test_event_model_rejects_non_dict_data():
    from models.event import EventModel

    # Act + Assert
    with pytest.raises(ValueError) as exc_info:
        EventModel.validate_event(
            {'operation': 'db', 'action': 'current', 'data': 'not-dict'}
        )

    assert str(exc_info.value) == 'Data debe ser un objeto JSON valido'
