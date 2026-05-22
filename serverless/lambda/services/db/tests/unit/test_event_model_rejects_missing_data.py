"""Modelo event.EventModel.validate_event — sin data.

Given un evento sin la clave 'data',
When se invoca EventModel.validate_event,
Then lanza un ValueError indicando que data es requerida.
"""

import pytest

pytestmark = pytest.mark.unit


def test_event_model_rejects_missing_data():
    from models.event import EventModel

    # Act + Assert
    with pytest.raises(ValueError) as exc_info:
        EventModel.validate_event({'operation': 'db', 'action': 'current'})

    assert str(exc_info.value) == 'Data es requerida'
