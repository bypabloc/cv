"""Modelo DowngradeModel.

Given un payload con un campo no declarado,
When se valida con DowngradeModel,
Then Pydantic lo rechaza (model_config extra='forbid').
"""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_downgrade_model_rejects_unknown_field():
    from models.db import DowngradeModel

    # Act + Assert
    with pytest.raises(ValidationError):
        DowngradeModel(target='-1', confirm=True, unexpected='x')
