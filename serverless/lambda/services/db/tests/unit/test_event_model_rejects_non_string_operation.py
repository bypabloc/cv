"""Modelo event.EventModel.validate_event — operation no string.

Given un evento cuya 'operation' no es un string,
When se invoca EventModel.validate_event,
Then lanza un ValueError indicando que falta la operacion.
"""

import pytest

pytestmark = pytest.mark.unit


def test_event_model_rejects_non_string_operation():
    from models.event import EventModel

    # Act + Assert
    with pytest.raises(ValueError) as exc_info:
        EventModel.validate_event(
            {'operation': 123, 'action': 'current', 'data': {}}
        )

    assert str(exc_info.value) == ('No se especifico la operacion a ejecutar')
