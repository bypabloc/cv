"""
Given un ContactItem persistido,
When conditional_update corre con una condicion que se cumple y otra que no,
Then la condicion satisfecha actualiza el item y la fallida devuelve None.
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models import ContactItem

pytestmark = pytest.mark.integration


def test_base_model_conditional_update_e2e(dynamodb_tables: None) -> None:
    """conditional_update aplica el SET solo si la condicion pasa."""
    # Arrange
    ContactItem(
        id='cond-1',
        created_at='2026-05-21T10:00:00+00:00',
        name='Pablo',
        email='x@example.com',
        message='Hola',
    ).save()

    # Act: condicion verdadera (name == 'Pablo') -> aplica.
    ok = ContactItem.conditional_update(
        'cond-1',
        condition='#n = :expected',
        condition_names={'#n': 'name'},
        condition_values={':expected': 'Pablo'},
        company='Acme',
    )
    # Condicion falsa (name == 'Otro') -> no aplica.
    failed = ContactItem.conditional_update(
        'cond-1',
        condition='#n = :expected',
        condition_names={'#n': 'name'},
        condition_values={':expected': 'Otro'},
        company='Beta',
    )

    # Assert
    assert ok is not None
    assert ok.company == 'Acme'
    assert failed is None
