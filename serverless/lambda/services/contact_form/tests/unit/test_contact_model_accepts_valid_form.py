"""Modelo ContactCreateModel — payload valido.

Given un payload con name/email/message validos y un bloque `_meta`,
When se valida con ContactCreateModel,
Then el modelo acepta el payload y `form_fields()` omite cf_token y _meta.
"""

import pytest

pytestmark = pytest.mark.unit


def test_contact_model_accepts_valid_form():
    from models.contact import ContactCreateModel

    # Arrange
    payload = {
        'name': 'Pablo Contreras',
        'email': 'user@example.com',
        'message': 'Hola, me interesa colaborar contigo.',
        'cf_token': 'x' * 30,
        'niche': 'fintech',
        '_meta': {
            'ip': '203.0.113.10',
            'country': 'CL',
            'user_agent': 'Mozilla/5.0',
            'bypass_secret': None,
        },
    }

    # Act
    model = ContactCreateModel.model_validate(payload)
    fields = model.form_fields()

    # Assert
    assert model.email == 'user@example.com'
    assert model.meta.ip == '203.0.113.10'
    assert fields == {
        'name': 'Pablo Contreras',
        'email': 'user@example.com',
        'message': 'Hola, me interesa colaborar contigo.',
        'niche': 'fintech',
    }
