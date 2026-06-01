"""
Given varios items con la misma partition key,
When se llama .query(partition_value),
Then devuelve todos los items de esa particion.
"""

from __future__ import annotations

import pytest
from boto3.dynamodb.conditions import Key
from shared.dynamodb.models.tracking import TrackingEventItem


def _event(session_id: str, page_id: str, created_at: str) -> TrackingEventItem:
    """Construye un TrackingEventItem minimo."""
    return TrackingEventItem(
        session_id=session_id,
        page_id=page_id,
        created_at=created_at,
        expires_at=1720000000,
        page_url='https://x.com',
        event_id=f'e-{page_id}',
        event_type_id='page_view',
    )


@pytest.mark.usefixtures('dynamodb_tables')
def test_query_returns_all_items_of_partition() -> None:
    """query() por partition key devuelve los items de esa sesion."""
    # Arrange
    _event('s1', 'p1', '2026-05-21T10:00:00+00:00').save()
    _event('s1', 'p2', '2026-05-21T10:01:00+00:00').save()
    _event('s2', 'p9', '2026-05-21T10:02:00+00:00').save()

    # Act
    results = TrackingEventItem.query('s1')

    # Assert
    assert len(results) == 2
    assert {r.page_id for r in results} == {'p1', 'p2'}


@pytest.mark.usefixtures('dynamodb_tables')
def test_query_with_sort_condition_filters_by_sort_key() -> None:
    """query() con sort_condition filtra por la sort key."""
    # Arrange
    _event('s1', 'p1', '2026-05-21T10:00:00+00:00').save()
    _event('s1', 'p2', '2026-05-21T10:01:00+00:00').save()

    # Act
    results = TrackingEventItem.query(
        's1', sort_condition=Key('page_id').eq('p2')
    )

    # Assert
    assert len(results) == 1
    assert results[0].page_id == 'p2'


@pytest.mark.usefixtures('dynamodb_tables')
def test_query_limit_caps_results() -> None:
    """query() con limit acota la cantidad de items."""
    # Arrange
    _event('s1', 'p1', '2026-05-21T10:00:00+00:00').save()
    _event('s1', 'p2', '2026-05-21T10:01:00+00:00').save()

    # Act
    results = TrackingEventItem.query('s1', limit=1)

    # Assert
    assert len(results) == 1
