"""Util validation.event.validate_event — ValidationError de Pydantic.

Given EventModel.validate_event que lanza un ValidationError de Pydantic,
When se invoca validate_event,
Then devuelve {is_valid: False} con code 1000 (pydantic_error) y un
     mensaje de error de estructura.
"""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_validate_event_reports_pydantic_validation_error():
    from models.db import MigrateModel
    from utils.validation.event import validate_event

    # Arrange: provocar un ValidationError real y reusarlo como side_effect.
    try:
        MigrateModel.model_validate({'unknown': 'x'})
        raise AssertionError('MigrateModel deberia rechazar el campo extra')
    except ValidationError as exc:
        pydantic_error = exc

    event = {'operation': 'db', 'action': 'current', 'data': {}}
    with patch(
        'utils.validation.event.EventModel.validate_event',
        side_effect=pydantic_error,
    ):
        # Act
        result = validate_event(event)

    # Assert
    assert result == {
        'is_valid': False,
        'code': 1000,
        'status': 1000,
        'message': 'Error de validacion de estructura',
        'data': {},
    }
