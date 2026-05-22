"""Modelo SeedModel.

Given un payload con un campo no declarado,
When se valida con SeedModel,
Then Pydantic lo rechaza (model_config extra='forbid').
"""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_seed_model_rejects_unknown_field():
    from models.db import SeedModel

    # Act + Assert
    with pytest.raises(ValidationError):
        SeedModel(unexpected='x')
