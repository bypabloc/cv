"""shared.db.repository.insert_contact.

Given una Session y un payload de contacto,
When se invoca insert_contact,
Then agrega a la Session una fila Contact con los campos del payload.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.models import Contact
from shared.db.repository import insert_contact

pytestmark = pytest.mark.unit


def test_insert_contact_adds_contact() -> None:
    # Arrange
    session = MagicMock()
    payload = {
        'id': 'c-1',
        'name': 'Pablo',
        'email': 'user@example.com',
        'message': 'hola',
    }

    # Act
    insert_contact(session, payload)

    # Assert
    assert session.add.call_count == 1
    added = session.add.call_args[0][0]
    assert isinstance(added, Contact)
    assert added.id == 'c-1'
    assert added.email == 'user@example.com'
