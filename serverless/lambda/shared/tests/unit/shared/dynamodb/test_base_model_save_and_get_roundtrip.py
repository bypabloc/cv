"""
Given el ORM y un mock_aws activo,
When un modelo hace .save() y luego .get(),
Then el item se persiste y se recupera identico (AC-5).
"""

from __future__ import annotations

import pytest

from shared.dynamodb import ContactItem, TrackingEventItem


@pytest.mark.usefixtures('dynamodb_tables')
def test_save_then_get_simple_pk_roundtrip() -> None:
    """save()/get() en una tabla de PK simple (contacts)."""
    # Arrange
    ContactItem(
        id='01HZ',
        created_at='2026-05-21T10:00:00+00:00',
        name='Pablo',
        email='pablo@example.com',
        message='Hola',
        company='Acme',
    ).save()

    # Act
    fetched = ContactItem.get('01HZ')

    # Assert
    assert fetched is not None
    assert fetched.name == 'Pablo'
    assert fetched.company == 'Acme'
    assert fetched.role is None


@pytest.mark.usefixtures('dynamodb_tables')
def test_save_then_get_composite_pk_roundtrip() -> None:
    """save()/get() en una tabla de PK compuesta (tracking)."""
    # Arrange
    TrackingEventItem(
        session_id='s1',
        page_id='p1',
        created_at='2026-05-21T10:00:00+00:00',
        expires_at=1720000000,
        page_url='https://x.com',
        event_id='e1',
        event_type_id='page_view',
    ).save()

    # Act
    fetched = TrackingEventItem.get('s1', 'p1')

    # Assert
    assert fetched is not None
    assert fetched.page_url == 'https://x.com'
    assert fetched.expires_at == 1720000000


@pytest.mark.usefixtures('dynamodb_tables')
def test_get_missing_item_returns_none() -> None:
    """get() de un item inexistente devuelve None."""
    # Act
    fetched = ContactItem.get('does-not-exist')

    # Assert
    assert fetched is None


@pytest.mark.usefixtures('dynamodb_tables')
def test_get_composite_pk_without_sort_value_raises() -> None:
    """get() en tabla con SK exige el sort_value."""
    # Act / Assert
    with pytest.raises(ValueError, match='sort_key'):
        TrackingEventItem.get('s1')


@pytest.mark.usefixtures('dynamodb_tables')
def test_delete_removes_item() -> None:
    """delete() elimina el item; get() posterior devuelve None."""
    # Arrange
    ContactItem(
        id='01HZ',
        created_at='2026-05-21T10:00:00+00:00',
        name='Pablo',
        email='pablo@example.com',
        message='Hola',
    ).save()

    # Act
    ContactItem.delete('01HZ')

    # Assert
    assert ContactItem.get('01HZ') is None


@pytest.mark.usefixtures('dynamodb_tables')
def test_update_sets_attributes() -> None:
    """update() setea atributos y devuelve el item ALL_NEW."""
    # Arrange
    ContactItem(
        id='01HZ',
        created_at='2026-05-21T10:00:00+00:00',
        name='Pablo',
        email='pablo@example.com',
        message='Hola',
    ).save()

    # Act
    updated = ContactItem.update('01HZ', niche='leader', company='Beta')

    # Assert
    assert updated.niche == 'leader'
    assert updated.company == 'Beta'
    assert updated.name == 'Pablo'
