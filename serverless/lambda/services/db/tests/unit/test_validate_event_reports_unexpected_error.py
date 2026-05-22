"""Util validation.event.validate_event — error inesperado.

Given EventModel.validate_event que lanza una excepcion que no es
     ValidationError ni ValueError,
When se invoca validate_event,
Then devuelve {is_valid: False} con code 6000 (unexpected_error) y un
     mensaje de error inesperado.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_validate_event_reports_unexpected_error():
    from utils.validation.event import validate_event

    # Arrange
    event = {'operation': 'db', 'action': 'current', 'data': {}}
    with patch(
        'utils.validation.event.EventModel.validate_event',
        side_effect=RuntimeError('fallo no controlado'),
    ):
        # Act
        result = validate_event(event)

    # Assert
    assert result == {
        'is_valid': False,
        'code': 6000,
        'status': 6000,
        'message': 'Error inesperado durante la validacion',
        'data': {},
    }
