"""Model CvQueryModel — niche invalido.

Given un niche que NO esta en la lista de niches validos,
When se llama normalized_niche,
Then devuelve None (sin filtro), no levanta error.
"""

import pytest

pytestmark = pytest.mark.unit


def test_cv_query_model_normalizes_invalid_niche():
    from models.cv import CvQueryModel

    # Arrange
    model = CvQueryModel(niche='nonexistent')

    # Act + Assert
    assert model.normalized_niche() is None


def test_cv_query_model_keeps_valid_niche():
    from models.cv import CvQueryModel

    model = CvQueryModel(niche='fintech')
    assert model.normalized_niche() == 'fintech'
