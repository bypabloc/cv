"""
Given un ContactItem con campos opcionales en None,
When se llama to_item(),
Then el dict resultante NO contiene esas claves (AC-1).
"""

from __future__ import annotations

from shared.dynamodb.models import ContactItem


def test_to_item_omits_none_optional_fields() -> None:
    """to_item() filtra los campos opcionales no provistos."""
    # Arrange
    item = ContactItem(
        id='01HZ',
        created_at='2026-05-21T10:00:00+00:00',
        name='Pablo',
        email='pablo@example.com',
        message='Hola',
    )

    # Act
    result = item.to_item()

    # Assert
    assert result == {
        'id': '01HZ',
        'created_at': '2026-05-21T10:00:00+00:00',
        'name': 'Pablo',
        'email': 'pablo@example.com',
        'message': 'Hola',
    }


def test_to_item_keeps_provided_optional_fields() -> None:
    """to_item() conserva los opcionales que SI tienen valor."""
    # Arrange
    item = ContactItem(
        id='01HZ',
        created_at='2026-05-21T10:00:00+00:00',
        name='Pablo',
        email='pablo@example.com',
        message='Hola',
        company='Acme',
        niche='fintech',
    )

    # Act
    result = item.to_item()

    # Assert
    assert result['company'] == 'Acme'
    assert result['niche'] == 'fintech'
    assert 'role' not in result
