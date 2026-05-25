"""Model CvQueryModel — alias `_meta`.

Given un payload con _meta (inyectado por http_handler),
When se construye el modelo,
Then se asigna a model.meta sin error y los demas campos se preservan.
"""

import pytest

pytestmark = pytest.mark.unit


def test_cv_query_model_accepts_meta_alias():
    from models.cv import CvQueryModel

    # Act
    model = CvQueryModel(
        niche='generic',
        locale='en',
        _meta={'ip': '1.2.3.4', 'country': 'CL'},
    )

    # Assert
    assert model.niche == 'generic'
    assert model.locale == 'en'
    assert model.meta.ip == '1.2.3.4'
    assert model.meta.country == 'CL'
