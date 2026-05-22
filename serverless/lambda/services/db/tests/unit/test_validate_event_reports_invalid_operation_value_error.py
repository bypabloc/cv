"""Util validation.event.validate_event — operacion invalida.

Given un evento con una action cuyo controller no existe (EventModel
     lanza un ValueError con 'no es valida'),
When se invoca validate_event,
Then devuelve {is_valid: False} con code 1001 (invalid_operation) y el
     mensaje original del ValueError.
"""

import pytest

pytestmark = pytest.mark.unit


def test_validate_event_reports_invalid_operation_value_error():
    from utils.validation.event import validate_event

    # Arrange: operation valida, action sin controller -> ValueError.
    event = {'operation': 'db', 'action': 'bogus', 'data': {}}

    # Act
    result = validate_event(event)

    # Assert
    assert result['is_valid'] is False
    assert result['code'] == 1001
    assert result['status'] == 1001
    assert 'no es valida' in result['message']
