"""
Given un ContactItem persistido con put_if_absent,
When un segundo put_if_absent corre con la misma partition key,
Then el primero escribe (True) y el segundo no sobreescribe (False).
"""

from __future__ import annotations

import pytest
from shared.dynamodb import ContactItem

pytestmark = pytest.mark.integration


def _contact(name: str) -> ContactItem:
    """Construye un ContactItem con id fijo y el nombre dado."""
    return ContactItem(
        id='dup-1',
        created_at='2026-05-21T10:00:00+00:00',
        name=name,
        email='x@example.com',
        message='Hola',
    )


def test_base_model_put_if_absent_e2e(dynamodb_tables: None) -> None:
    """put_if_absent: 1o escribe, 2o falla la condicion sin sobreescribir."""
    # Act
    first = _contact('Original').put_if_absent()
    second = _contact('Overwrite').put_if_absent()
    stored = ContactItem.get('dup-1')

    # Assert
    assert first is True
    assert second is False
    assert stored is not None
    assert stored.name == 'Original'
