"""Modelo event.EventModel.validate_event — evento que no es dict.

Given un evento que no es un objeto JSON,
When se invoca EventModel.validate_event,
Then lanza un ValueError indicando que el evento debe ser un objeto.
"""

import pytest

pytestmark = pytest.mark.unit


def test_event_model_rejects_non_dict_event():
    from models.event import EventModel

    # Act + Assert
    with pytest.raises(ValueError) as exc_info:
        EventModel.validate_event('not a dict')

    assert str(exc_info.value) == 'Event debe ser un objeto JSON valido'
