"""Modelo TrackEventModel — utm_* required pero acepta string vacio.

Given un body de tracking con utm_source/medium/campaign/content = '',
When TrackEventModel.model_validate corre,
Then la validacion pasa y los 4 campos quedan como string vacio.
Spec: el frontend SIEMPRE manda los 4 utm_* (string vacio cuando no
hay query param). [AC-9]
"""

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_track_model_accepts_empty_utm():
    from models.tracking import TrackEventModel

    # Arrange: body con utm_* todos vacios (default de valid_body())
    body = valid_body()
    assert body['utm_source'] == ''
    assert body['utm_medium'] == ''

    # Act
    model = TrackEventModel.model_validate(body)

    # Assert
    assert model.utm_source == ''
    assert model.utm_medium == ''
    assert model.utm_campaign == ''
    assert model.utm_content == ''
    # utm_term sigue siendo opcional
    assert model.utm_term is None
