"""shared.lambda_kit.validation.event.validate_event.

Given un evento que no es un dict,
When se invoca validate_event,
Then devuelve {is_valid: False} con code 1000.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.event_model import build_event_model
from shared.lambda_kit.validation.event import validate_event

pytestmark = pytest.mark.unit


def test_validate_event_rejects_non_dict() -> None:
    # Arrange
    event_model = build_event_model({})

    # Act
    result = validate_event(['not', 'a', 'dict'], event_model)

    # Assert
    assert result == {
        'is_valid': False,
        'code': 1000,
        'status': 1000,
        'message': 'Event debe ser un objeto JSON valido',
        'data': {},
    }
