"""Util validation.event.validate_event — evento que no es dict.

Given un evento que no es un objeto (una lista),
When se invoca validate_event,
Then devuelve {is_valid: False} con code 1000 y un mensaje de tipo
     invalido.
"""

import pytest

pytestmark = pytest.mark.unit


def test_validate_event_rejects_non_dict_event():
    from utils.validation.event import validate_event

    # Act
    result = validate_event(['not', 'a', 'dict'])

    # Assert
    assert result == {
        'is_valid': False,
        'code': 1000,
        'status': 1000,
        'message': 'Event debe ser un objeto JSON valido',
        'data': {},
    }
