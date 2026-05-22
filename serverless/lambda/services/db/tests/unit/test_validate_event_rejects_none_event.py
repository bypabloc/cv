"""Util validation.event.validate_event — evento nulo.

Given un evento None,
When se invoca validate_event,
Then devuelve {is_valid: False} con code 1000 y un mensaje de evento nulo.
"""

import pytest

pytestmark = pytest.mark.unit


def test_validate_event_rejects_none_event():
    from utils.validation.event import validate_event

    # Act
    result = validate_event(None)

    # Assert
    assert result == {
        'is_valid': False,
        'code': 1000,
        'status': 1000,
        'message': 'Event no puede ser nulo',
        'data': {},
    }
