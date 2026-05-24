"""Modelo TrackEventModel — rechaza body sin page_path.

Given un body de tracking sin la clave `page_path`,
When TrackEventModel.model_validate corre,
Then lanza ValidationError mencionando page_path como missing. [AC-1]
"""

import pytest
from pydantic import ValidationError

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_track_model_rejects_missing_page_path():
    from models.tracking import TrackEventModel

    # Arrange: quitar page_path del body
    body = valid_body()
    del body['page_path']

    # Act + Assert
    with pytest.raises(ValidationError) as exc_info:
        TrackEventModel.model_validate(body)

    errors = exc_info.value.errors()
    missing_fields = {e['loc'][0] for e in errors if e['type'] == 'missing'}
    assert 'page_path' in missing_fields
