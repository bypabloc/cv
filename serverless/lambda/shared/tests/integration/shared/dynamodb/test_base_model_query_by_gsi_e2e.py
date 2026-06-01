"""
Given varios TrackingEventItem con distinto `niche` persistidos,
When se hace query sobre el GSI 'niche-created_at-index',
Then solo devuelve los items del niche consultado, ordenados por la SK.
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models.tracking import TrackingEventItem

pytestmark = pytest.mark.integration


def _event(*, session: str, page: str, niche: str, created: str) -> None:
    """Persiste un TrackingEventItem minimo con el niche dado."""
    TrackingEventItem(
        session_id=session,
        page_id=page,
        created_at=created,
        expires_at=1_720_000_000,
        page_url='https://x.com',
        event_id=f'e-{page}',
        event_type_id='page_view',
        niche=niche,
    ).save()


def test_base_model_query_by_gsi_e2e(dynamodb_tables: None) -> None:
    """query(index_name=...) filtra por la PK del GSI."""
    # Arrange
    _event(session='s1', page='p1', niche='leader', created='2026-05-01')
    _event(session='s2', page='p2', niche='leader', created='2026-05-02')
    _event(session='s3', page='p3', niche='fintech', created='2026-05-03')

    # Act
    leader_events = TrackingEventItem.query(
        'leader', index_name='niche-created_at-index'
    )

    # Assert
    assert len(leader_events) == 2
    assert {e.event_id for e in leader_events} == {'e-p1', 'e-p2'}
