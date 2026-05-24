"""Modelo TrackEventModel — rechaza body sin viewport_width/height.

Given un body de tracking sin viewport_width o viewport_height,
When TrackEventModel.model_validate corre,
Then ValidationError lista AMBOS como missing. [AC-1]
"""

import pytest
from pydantic import ValidationError

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_track_model_rejects_missing_viewport():
    from models.tracking import TrackEventModel

    # Arrange: quitar viewport
    body = valid_body()
    del body['viewport_width']
    del body['viewport_height']

    # Act + Assert
    with pytest.raises(ValidationError) as exc_info:
        TrackEventModel.model_validate(body)

    errors = exc_info.value.errors()
    missing = {e['loc'][0] for e in errors if e['type'] == 'missing'}
    assert {'viewport_width', 'viewport_height'} <= missing
