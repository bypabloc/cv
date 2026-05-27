"""Modelo TrackEventModel — tracking_payload() limpia cf_token y meta.

Given un body con cf_token y un meta,
When se invoca tracking_payload() sobre el modelo validado,
Then el dict resultante no contiene cf_token ni meta ni valores None.
"""

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_track_model_tracking_payload_excludes_cf_token_and_meta():
    from models.tracking import TrackEventModel

    # Arrange
    data = {
        **valid_body(cf_token='cf-dummy'),
        'meta': {'ip': '1.2.3.4', 'country': 'CL', 'user_agent': 'UA'},
    }
    model = TrackEventModel.model_validate(data)

    # Act
    payload = model.tracking_payload()

    # Assert: cf_token + meta excluidos; el resto SI presente (page_title
    # ahora es required en el modelo, no se omite por defecto vacio).
    assert 'cf_token' not in payload
    assert 'meta' not in payload
    assert payload['page_title'] == 'Projects'
    assert payload['session_id'] == valid_body()['session_id']
