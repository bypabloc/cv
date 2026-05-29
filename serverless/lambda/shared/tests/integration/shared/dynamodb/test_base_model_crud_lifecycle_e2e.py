"""
Given las 5 tablas del backend creadas por el ORM en DynamoDB,
When un ContactItem recorre save -> get -> update -> delete,
Then cada operacion se observa contra DynamoDB real y el ciclo cierra
     con get() devolviendo None.
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models import ContactItem

pytestmark = pytest.mark.integration


def test_base_model_crud_lifecycle_e2e(dynamodb_tables: None) -> None:
    """Ciclo CRUD completo de un ContactItem contra DynamoDB."""
    # Arrange
    ContactItem(
        id='01HZ-A',
        created_at='2026-05-21T10:00:00+00:00',
        name='Pablo',
        email='pablo@example.com',
        message='Hola',
    ).save()

    # Act
    fetched = ContactItem.get('01HZ-A')
    updated = ContactItem.update('01HZ-A', company='Acme', niche='leader')
    ContactItem.delete('01HZ-A')
    after_delete = ContactItem.get('01HZ-A')

    # Assert
    assert fetched is not None
    assert fetched.name == 'Pablo'
    assert updated.company == 'Acme'
    assert updated.niche == 'leader'
    assert after_delete is None
