"""
Given total=120 visitas y una pagina de 50 (offset 0) con 50 filas,
When se invoca visits_service.list (NO cacheado, llamada directa),
Then devuelve el shape de paginacion con has_more=True (50 < 120).
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import services.visits_service as visits_service


def test_visits_list_when_more_rows_then_has_more_true(mocker):
    # Arrange: 50 filas identicas + total 120 -> has_more = (0+50) < 120.
    started = datetime(2026, 5, 1, 10, 30, tzinfo=UTC)
    ended = datetime(2026, 5, 1, 10, 45, tzinfo=UTC)
    row = MagicMock(name='VisitRow')
    row.visit_id = 'v-1'
    row.session_id = 's-1'
    row.started_at = started
    row.ended_at = ended
    row.event_count = 7
    row.ip = '203.0.113.42'
    row.country = 'AR'
    row.utm_source = 'google'
    row.utm_medium = 'cpc'
    row.utm_campaign = 'launch'
    row.referrer = 'https://google.com'
    row.landing_page_path = '/home'
    row.niche = 'fintech'

    session = MagicMock(name='SQLAlchemySession')
    session.scalar.return_value = 120
    session.execute.return_value.all.return_value = [row] * 50
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(visits_service, 'db_session', return_value=cm)

    # Act
    result = visits_service.list(
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
        'visit_id': 'v-1',
        'session_id': 's-1',
        'started_at': '2026-05-01T10:30:00+00:00',
        'ended_at': '2026-05-01T10:45:00+00:00',
        'event_count': 7,
        'ip': '203.0.113.42',
        'country': 'AR',
        'utm_source': 'google',
        'utm_medium': 'cpc',
        'utm_campaign': 'launch',
        'referrer': 'https://google.com',
        'landing_page_path': '/home',
        'niche': 'fintech',
    }
