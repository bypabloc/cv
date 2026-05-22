"""Modelo ContactCreateModel — email invalido.

Given un payload con un email mal formado,
When se valida con ContactCreateModel,
Then Pydantic levanta ValidationError.
"""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_contact_model_rejects_invalid_email():
    from models.contact import ContactCreateModel

    # Arrange
    payload = {
        'name': 'Pablo Contreras',
        'email': 'not-an-email',
        'message': 'Hola, me interesa colaborar contigo.',
        'cf_token': 'x' * 30,
        '_meta': {'ip': '203.0.113.10'},
    }

    # Act / Assert
    with pytest.raises(ValidationError):
        ContactCreateModel.model_validate(payload)
