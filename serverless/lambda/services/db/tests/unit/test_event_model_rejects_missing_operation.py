"""Modelo event.EventModel.validate_event — sin operation.

Given un evento sin la clave 'operation',
When se invoca EventModel.validate_event,
Then lanza un ValueError indicando que falta la operacion.
"""

import pytest

pytestmark = pytest.mark.unit


def test_event_model_rejects_missing_operation():
    from models.event import EventModel

    # Act + Assert
    with pytest.raises(ValueError) as exc_info:
        EventModel.validate_event({'action': 'current', 'data': {}})

    assert str(exc_info.value) == ('No se especifico la operacion a ejecutar')
