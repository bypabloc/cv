"""Service contact_service.parse_recipients — parsing del SSM owner-email.

Given un parametro owner-email con varios correos en CSV, con espacios y
     comas sobrantes,
When se invoca parse_recipients,
Then devuelve la lista de direcciones limpias, sin entradas vacias.
"""

import pytest

pytestmark = pytest.mark.unit


def test_contact_service_parse_recipients_splits_csv():
    from services.contact_service import parse_recipients

    # Act
    result = parse_recipients(' a@x.com , b@y.com ,, c@z.com,')

    # Assert
    assert result == ['a@x.com', 'b@y.com', 'c@z.com']
