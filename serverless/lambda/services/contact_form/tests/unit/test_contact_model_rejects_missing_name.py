"""Modelo ContactCreateModel — body sin campo obligatorio.

Given un payload sin el campo obligatorio `name`,
When se valida con ContactCreateModel,
Then Pydantic levanta ValidationError.
"""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_contact_model_rejects_missing_name():
    from models.contact import ContactCreateModel

    # Arrange
    payload = {
        'email': 'user@example.com',
        'message': 'Mensaje de prueba sin nombre.',
        'cf_token': 'x' * 30,
        '_meta': {'ip': '203.0.113.10'},
    }

    # Act / Assert
    with pytest.raises(ValidationError):
        ContactCreateModel.model_validate(payload)
