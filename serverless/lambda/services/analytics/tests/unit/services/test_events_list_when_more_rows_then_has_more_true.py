"""
Given total=120 eventos y una pagina de 50 (offset 0) con 50 filas,
When se invoca events_service.list (NO cacheado, llamada directa),
Then devuelve el shape de paginacion con has_more=True (50 < 120).
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import services.events_service as events_service


def test_events_list_when_more_rows_then_has_more_true(mocker):
    # Arrange: 50 filas identicas + total 120 -> has_more = (0+50) < 120.
    created = datetime(2026, 5, 1, 10, 30, tzinfo=UTC)
    row = MagicMock(name='EventRow')
    row.created_at = created
    row.visit_id = 'v-1'
    row.page_id = 'p-1'
    row.session_id = 's-1'
    row.page_path = '/home'
    row.niche = 'fintech'
    row.viewport_width = 1920
    row.viewport_height = 1080
    row.event_type = 'click'
    row.event_props = {'x': 1}

    session = MagicMock(name='SQLAlchemySession')
    session.scalar.return_value = 120
    session.execute.return_value.all.return_value = [row] * 50
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(events_service, 'db_session', return_value=cm)

    # Act
    result = events_service.list(
        date_from=datetime(2026, 4, 27).date(),
        date_to=datetime(2026, 5, 28).date(),
        page=1,
        page_size=50,
        offset=0,
    )

    # Assert: shape de paginacion exacto.
    assert result['page'] == 1
    assert result['page_size'] == 50
    assert result['total'] == 120
    assert result['has_more'] is True
    assert len(result['items']) == 50
    assert result['items'][0] == {
        'created_at': '2026-05-01T10:30:00+00:00',
        'visit_id': 'v-1',
        'page_id': 'p-1',
        'session_id': 's-1',
        'page_path': '/home',
        'niche': 'fintech',
        'viewport_width': 1920,
        'viewport_height': 1080,
        'event_type': 'click',
        'event_props': {'x': 1},
    }
