"""Modelo DowngradeModel.

Given un payload sin 'target',
When se valida con DowngradeModel,
Then Pydantic lo rechaza ('target' es obligatorio).
"""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_downgrade_model_requires_target():
    from models.db import DowngradeModel

    # Act + Assert
    with pytest.raises(ValidationError):
        DowngradeModel(confirm=True)
