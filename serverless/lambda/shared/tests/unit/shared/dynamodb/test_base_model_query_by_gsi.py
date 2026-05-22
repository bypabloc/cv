"""
Given una tabla con el GSI niche-created_at-index,
When se llama .query(niche, index_name='niche-created_at-index'),
Then devuelve los items de ese nicho via el indice (AC-10).
"""

from __future__ import annotations

import pytest

from shared.dynamodb import TrackingEventItem


def _event(
    session_id: str, page_id: str, niche: str, created_at: str
) -> TrackingEventItem:
    """Construye un TrackingEventItem con niche poblado."""
    return TrackingEventItem(
        session_id=session_id,
        page_id=page_id,
        created_at=created_at,
        expires_at=1720000000,
        page_url='https://x.com',
        event_id=f'e-{page_id}',
        event_type_id='page_view',
        niche=niche,
    )


@pytest.mark.usefixtures('dynamodb_tables')
def test_query_by_gsi_returns_items_of_niche() -> None:
    """query() via GSI devuelve solo los items del nicho consultado."""
    # Arrange
    _event('s1', 'p1', 'fintech', '2026-05-21T10:00:00+00:00').save()
    _event('s2', 'p2', 'fintech', '2026-05-21T10:01:00+00:00').save()
    _event('s3', 'p3', 'leader', '2026-05-21T10:02:00+00:00').save()

    # Act
    results = TrackingEventItem.query(
        'fintech', index_name='niche-created_at-index'
    )

    # Assert
    assert len(results) == 2
    assert {r.niche for r in results} == {'fintech'}


@pytest.mark.usefixtures('dynamodb_tables')
def test_query_unknown_gsi_raises() -> None:
    """query() con un GSI inexistente es un error de programacion."""
    # Act / Assert
    with pytest.raises(ValueError, match='GSI desconocido'):
        TrackingEventItem.query('fintech', index_name='no-such-index')
