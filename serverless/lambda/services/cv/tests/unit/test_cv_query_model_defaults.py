"""Model CvQueryModel — defaults.

Given un payload vacio,
When se construye CvQueryModel,
Then niche es None y locale es 'es' (defaults).
"""

import pytest

pytestmark = pytest.mark.unit


def test_cv_query_model_defaults():
    from models.cv import CvQueryModel

    # Act
    model = CvQueryModel()

    # Assert
    assert model.niche is None
    assert model.locale == 'es'
    assert model.normalized_niche() is None
