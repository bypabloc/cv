"""
Given varios TrackingEventItem que comparten session_id (PK compuesta),
When se hace query por la partition key con un sort_condition begins_with,
Then devuelve solo los items de esa sesion cuyo page_id matchea el prefijo.
"""

from __future__ import annotations

import pytest
from boto3.dynamodb.conditions import Key
from shared.dynamodb import TrackingEventItem

pytestmark = pytest.mark.integration


def _event(*, session: str, page: str) -> None:
    """Persiste un TrackingEventItem minimo."""
    TrackingEventItem(
        session_id=session,
        page_id=page,
        created_at='2026-05-21',
        expires_at=1_720_000_000,
        page_url='https://x.com',
        event_id=f'e-{page}',
        event_type_id='page_view',
    ).save()


def test_base_model_query_by_partition_key_e2e(
    dynamodb_tables: None,
) -> None:
    """query con sort_condition begins_with sobre la SK."""
    # Arrange
    _event(session='sess-1', page='home-1')
    _event(session='sess-1', page='home-2')
    _event(session='sess-1', page='about-1')
    _event(session='sess-2', page='home-9')

    # Act
    home_pages = TrackingEventItem.query(
        'sess-1', sort_condition=Key('page_id').begins_with('home')
    )

    # Assert
    assert len(home_pages) == 2
    assert {e.page_id for e in home_pages} == {'home-1', 'home-2'}
