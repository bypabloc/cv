"""shared.lambda_kit.validation.event.validate_event.

Given un evento cuya operacion no resuelve a ningun controller,
When se invoca validate_event,
Then devuelve {is_valid: False} con code 1001 (invalid_operation).
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.event_model import build_event_model
from shared.lambda_kit.validation.event import validate_event

pytestmark = pytest.mark.unit


def test_validate_event_reports_invalid_operation() -> None:
    # Arrange: OPERATIONS vacio -> el controller nunca resuelve
    event_model = build_event_model({})
    event = {
        'operation': 'unknown',
        'action': 'create',
        'data': {},
    }

    # Act
    result = validate_event(event, event_model)

    # Assert
    assert result['is_valid'] is False
    assert result['code'] == 1001
