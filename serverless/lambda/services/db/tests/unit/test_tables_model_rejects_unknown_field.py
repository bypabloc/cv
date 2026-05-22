"""Modelo TablesModel.

Given un payload con un campo no declarado,
When se valida con TablesModel,
Then Pydantic lo rechaza (model_config extra='forbid').
"""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_tables_model_rejects_unknown_field():
    from models.db import TablesModel

    # Act + Assert
    with pytest.raises(ValidationError):
        TablesModel(unexpected='x')
