"""Modelo TrackEventModel — body sin session_id.

Given un body de tracking sin el campo requerido session_id,
When se valida con TrackEventModel,
Then Pydantic lanza ValidationError.
"""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_track_model_rejects_missing_session_id():
    from models.tracking import TrackEventModel

    # Arrange
    data = {
        'event_id': 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
        'event_type_id': '019e372b-e0a7-7154-8279-8829bcf6a08c',
        'page_url': 'https://the-full-stack.com/',
    }

    # Act / Assert
    with pytest.raises(ValidationError):
        TrackEventModel.model_validate(data)
