"""Util validation.event.validate_event — evento valido.

Given un evento bien formado {operation: 'db', action: 'current', data},
When se invoca validate_event,
Then devuelve {is_valid: True, code: 0} con el EventModel resuelto.
"""

import pytest
from models.event import EventModel

pytestmark = pytest.mark.unit


def test_validate_event_returns_validated_event_when_ok():
    from utils.validation.event import validate_event

    # Arrange
    event = {'operation': 'db', 'action': 'current', 'data': {}}

    # Act
    result = validate_event(event)

    # Assert
    assert result['is_valid'] is True
    assert result['code'] == 0
    assert isinstance(result['data'], EventModel)
