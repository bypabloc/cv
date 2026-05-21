"""Modelo TrackEventModel — event_id que no es un UUID valido.

Given un body con un event_id de longitud valida pero que no es un UUID,
When se valida con TrackEventModel,
Then el field_validator de UUID lanza ValidationError.
"""

import pytest
from pydantic import ValidationError

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_track_model_rejects_malformed_event_id():
    from models.tracking import TrackEventModel

    # Arrange: 32 chars pero no es un UUID hex valido.
    data = valid_body(event_id='zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz')

    # Act / Assert
    with pytest.raises(ValidationError):
        TrackEventModel.model_validate(data)
