"""
Given el mismo input de un contacto,
When se arma el Item con ContactItem.to_item() y con la logica vieja de
  save_contact (for-loop de campos opcionales),
Then ambos Items son identicos clave-a-clave (AC-7).

Este test de regresion garantiza que migrar contact_service a ContactItem
NO cambia el item que se escribe en DynamoDB.
"""

from __future__ import annotations

from typing import Any

from shared.dynamodb import ContactItem

# Campos opcionales del contacto, EN EL ORDEN del codigo viejo
# (contact_service.save_contact).
_LEGACY_OPTIONAL_FIELDS = (
    'company',
    'role',
    'service_type',
    'budget',
    'timeline',
    'niche',
    'session_id',
)


def _legacy_build_item(
    contact_id: str, created_at: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Replica EXACTA del armado de Item de save_contact (codigo viejo)."""
    item: dict[str, Any] = {
        'id': contact_id,
        'created_at': created_at,
        'name': payload['name'],
        'email': payload['email'],
        'message': payload['message'],
    }
    for optional_field in _LEGACY_OPTIONAL_FIELDS:
        value = payload.get(optional_field)
        if value:
            item[optional_field] = value
    return item


def test_contact_item_to_item_matches_legacy_minimal() -> None:
    """Item identico cuando solo hay campos obligatorios."""
    # Arrange
    payload = {
        'name': 'Pablo',
        'email': 'pablo@example.com',
        'message': 'Hola',
    }
    contact_id = '01HZ'
    created_at = '2026-05-21T10:00:00+00:00'

    # Act
    orm_item = ContactItem(
        id=contact_id, created_at=created_at, **payload
    ).to_item()
    legacy_item = _legacy_build_item(contact_id, created_at, payload)

    # Assert
    assert orm_item == legacy_item


def test_contact_item_to_item_matches_legacy_full() -> None:
    """Item identico con todos los campos opcionales presentes."""
    # Arrange
    payload = {
        'name': 'Pablo',
        'email': 'pablo@example.com',
        'message': 'Hola',
        'company': 'Acme',
        'role': 'CTO',
        'service_type': 'consulting',
        'budget': '10k',
        'timeline': 'Q3',
        'niche': 'fintech',
        'session_id': 'sess-1',
    }
    contact_id = '01HZ'
    created_at = '2026-05-21T10:00:00+00:00'

    # Act
    orm_item = ContactItem(
        id=contact_id, created_at=created_at, **payload
    ).to_item()
    legacy_item = _legacy_build_item(contact_id, created_at, payload)

    # Assert
    assert orm_item == legacy_item
