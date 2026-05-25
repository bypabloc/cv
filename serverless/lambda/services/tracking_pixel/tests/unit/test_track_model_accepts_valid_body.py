"""Modelo TrackEventModel — body de tracking valido.

Given un body de tracking con todos los campos requeridos y un `meta`,
When se valida con TrackEventModel,
Then la instancia conserva los campos y expone el `meta` con la IP.
"""

import pytest

from tests.unit._helpers import (
    EVENT_ID,
    EVENT_TYPE_ID,
    SESSION_ID,
    valid_body,
)

pytestmark = pytest.mark.unit


def test_track_model_accepts_valid_body():
    from models.tracking import TrackEventModel

    # Arrange
    data = {
        **valid_body(),
        'meta': {'ip': '1.2.3.4', 'country': 'CL', 'user_agent': 'UA'},
    }

    # Act
    model = TrackEventModel.model_validate(data)

    # Assert
    assert model.session_id == SESSION_ID
    assert model.event_id == EVENT_ID
    assert model.event_type_id == EVENT_TYPE_ID
    assert model.meta.ip == '1.2.3.4'
    assert model.meta.country == 'CL'
