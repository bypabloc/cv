"""Modelo event.EventModel — model_dump y model_dump_json.

Given un EventModel resuelto desde un evento valido,
When se invocan model_dump y model_dump_json,
Then model_dump devuelve {operation, action, data} y model_dump_json el
     mismo contenido serializado a JSON.
"""

import json

import pytest

pytestmark = pytest.mark.unit


def test_event_model_serializes_with_model_dump():
    from models.event import EventModel

    # Arrange
    event = {
        'operation': 'db',
        'action': 'migrate',
        'data': {'target': 'head'},
    }
    model = EventModel.validate_event(event)

    # Act
    as_dict = model.model_dump()
    as_json = model.model_dump_json()

    # Assert
    assert as_dict == {
        'operation': 'db',
        'action': 'migrate',
        'data': {'target': 'head'},
    }
    assert json.loads(as_json) == {
        'operation': 'db',
        'action': 'migrate',
        'data': {'target': 'head'},
    }
