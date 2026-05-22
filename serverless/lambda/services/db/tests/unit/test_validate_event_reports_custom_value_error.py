"""Util validation.event.validate_event — ValueError de validacion custom.

Given un evento al que le falta la clave 'data' (EventModel lanza un
     ValueError sin el texto 'no es valida'),
When se invoca validate_event,
Then devuelve {is_valid: False} con code 1000 (custom_validation_error) y
     el mensaje original del ValueError.
"""

import pytest

pytestmark = pytest.mark.unit


def test_validate_event_reports_custom_value_error():
    from utils.validation.event import validate_event

    # Arrange: sin 'data' -> EventModel lanza 'Data es requerida'.
    event = {'operation': 'db', 'action': 'current'}

    # Act
    result = validate_event(event)

    # Assert
    assert result['is_valid'] is False
    assert result['code'] == 1000
    assert result['status'] == 1000
    assert result['message'] == 'Data es requerida'
