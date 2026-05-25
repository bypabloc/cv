"""shared.lambda_kit.event_model.build_event_model.

Given un evento sin la clave operation,
When EventModel.validate_event lo procesa,
Then lanza ValueError indicando que falta la operacion.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.event_model import build_event_model

pytestmark = pytest.mark.unit


def test_event_model_rejects_missing_operation() -> None:
    # Arrange
    event_model = build_event_model({})

    # Act + Assert
    with pytest.raises(ValueError, match='operacion a ejecutar'):
        event_model.validate_event({'action': 'create', 'data': {}})
