"""shared.lambda_kit.event_model.build_event_model.

Given un evento sin la clave data,
When EventModel.validate_event lo procesa,
Then lanza ValueError indicando que data es requerida.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.event_model import build_event_model

pytestmark = pytest.mark.unit


def test_event_model_rejects_missing_data() -> None:
    # Arrange
    event_model = build_event_model({})

    # Act + Assert
    with pytest.raises(ValueError, match='Data es requerida'):
        event_model.validate_event(
            {'operation': 'demo', 'action': 'create'}
        )
