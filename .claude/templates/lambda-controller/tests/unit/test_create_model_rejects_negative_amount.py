"""
ExampleCreateModel: el validador de 'amount' rechaza montos no positivos.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

import pytest
from pydantic import ValidationError

from models.example import ExampleCreateModel


def test_create_model_rejects_negative_amount():
    """
    Given un payload de create con amount negativo,
    When se valida con ExampleCreateModel,
    Then se lanza ValidationError.
    """
    with pytest.raises(ValidationError):
        ExampleCreateModel(resource_id='R-1', amount=-5)
