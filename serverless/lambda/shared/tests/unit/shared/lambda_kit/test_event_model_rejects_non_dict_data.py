"""shared.lambda_kit.event_model.build_event_model.

Given un evento cuya data no es un dict,
When EventModel.validate_event lo procesa,
Then lanza ValueError indicando que data debe ser un objeto JSON.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.event_model import build_event_model

pytestmark = pytest.mark.unit


def test_event_model_rejects_non_dict_data() -> None:
    # Arrange
    event_model = build_event_model({})
    event = {'operation': 'demo', 'action': 'create', 'data': 'nope'}

    # Act + Assert
    with pytest.raises(ValueError, match='Data debe ser un objeto'):
        event_model.validate_event(event)
