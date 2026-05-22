"""Modelo ContactCreateModel — sanitizacion XSS del mensaje.

Given un payload cuyo `message` contiene HTML,
When se valida con ContactCreateModel,
Then el HTML queda escapado (prevencion de XSS en el render del email).
"""

import pytest

pytestmark = pytest.mark.unit


def test_contact_model_sanitizes_html_in_message():
    from models.contact import ContactCreateModel

    # Arrange
    payload = {
        'name': 'Pablo Contreras',
        'email': 'user@example.com',
        'message': 'Hola <script>alert(1)</script> hola hola',
        'cf_token': 'x' * 30,
        '_meta': {'ip': '203.0.113.10'},
    }

    # Act
    model = ContactCreateModel.model_validate(payload)

    # Assert
    assert '<script>' not in model.message
    assert '&lt;script&gt;' in model.message
