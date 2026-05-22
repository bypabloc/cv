"""shared.lambda_kit.dispatch.run_controller.

Given un evento sintetico cuya operacion no resuelve a un controller,
When se invoca run_controller,
Then devuelve un DispatchResult con stage='validation' e is_valid=False.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.dispatch import run_controller
from shared.lambda_kit.event_model import build_event_model

pytestmark = pytest.mark.unit


def test_dispatch_returns_validation_stage_on_invalid_event() -> None:
    # Arrange: OPERATIONS vacio -> ningun controller resuelve
    event_model = build_event_model({})
    event = {'operation': 'unknown', 'action': 'create', 'data': {}}

    # Act
    result = run_controller(event, event_model)

    # Assert
    assert result.stage == 'validation'
    assert result.is_valid is False
    assert result.code == 1001
