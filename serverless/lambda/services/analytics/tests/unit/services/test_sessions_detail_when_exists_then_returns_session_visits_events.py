"""
Given una sesion existente con 1 visita y 5 eventos,
When se invoca sessions_service.detail (sin cache, llamada directa),
Then devuelve {session, visits, events_count} con el shape esperado (AC-12).
"""

from datetime import datetime
from unittest.mock import MagicMock

import services.sessions_service as sessions_service


def test_sessions_detail_when_exists_then_returns_session_visits_events(mocker):
    # Arrange: row de sesion, row de visita y count de eventos.
    session_row = MagicMock(name='SessionRow')
    session_row.session_id = 'sess-1'
    session_row.first_seen_at = datetime(2026, 5, 1, 10, 0, 0)
    session_row.last_seen_at = datetime(2026, 5, 1, 11, 0, 0)
    session_row.browser = 'Chrome'
    session_row.browser_version = '120'
    session_row.os = 'Windows'
    session_row.device_type = 'desktop'

    visit_row = MagicMock(name='VisitRow')
    visit_row.visit_id = 'visit-1'
    visit_row.started_at = datetime(2026, 5, 1, 10, 0, 0)
    visit_row.ended_at = datetime(2026, 5, 1, 10, 30, 0)
    visit_row.event_count = 5
    visit_row.ip = '203.0.113.42'
    visit_row.country = 'AR'
    visit_row.utm_source = 'google'
    visit_row.utm_medium = 'cpc'
    visit_row.utm_campaign = 'launch'
    visit_row.referrer = 'https://google.com'
    visit_row.landing_page_path = '/fintech'
    visit_row.niche = 'fintech'

    session = MagicMock(name='SQLAlchemySession')
    session_proxy = MagicMock(name='SessionProxy')
    session_proxy.first.return_value = session_row
    visits_proxy = MagicMock(name='VisitsProxy')
    visits_proxy.all.return_value = [visit_row]
    session.execute.side_effect = [session_proxy, visits_proxy]
    session.scalar.return_value = 5
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(sessions_service, 'db_session', return_value=cm)

    # Act
    result = sessions_service.detail(session_id='sess-1')

    # Assert
    assert result == {
        'session': {
            'session_id': 'sess-1',
            'first_seen_at': '2026-05-01T10:00:00',
            'last_seen_at': '2026-05-01T11:00:00',
            'browser': 'Chrome',
            'browser_version': '120',
            'os': 'Windows',
            'device_type': 'desktop',
        },
        'visits': [
            {
                'visit_id': 'visit-1',
                'started_at': '2026-05-01T10:00:00',
                'ended_at': '2026-05-01T10:30:00',
                'event_count': 5,
                'ip': '203.0.113.42',
                'country': 'AR',
                'utm_source': 'google',
                'utm_medium': 'cpc',
                'utm_campaign': 'launch',
                'referrer': 'https://google.com',
                'landing_page_path': '/fintech',
                'niche': 'fintech',
            }
        ],
        'events_count': 5,
    }
