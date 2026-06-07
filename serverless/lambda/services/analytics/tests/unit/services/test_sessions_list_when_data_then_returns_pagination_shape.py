"""
Given 2 sesiones en el rango y total=2,
When se invoca sessions_service.list (sin cache, llamada directa),
Then devuelve {items, page, page_size, total, has_more} con has_more False.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import services.sessions_service as sessions_service


def test_sessions_list_when_data_then_returns_pagination_shape(mocker):
    # Arrange: db_session context manager con total + 2 rows.
    row1 = MagicMock(name='Row1')
    row1.session_id = 'sess-1'
    row1.first_seen_at = datetime(2026, 5, 1, 10, 0, 0)
    row1.last_seen_at = datetime(2026, 5, 1, 11, 0, 0)
    row1.browser = 'Chrome'
    row1.browser_version = '120'
    row1.os = 'Windows'
    row1.device_type = 'desktop'
    row1.visits_count = 3

    row2 = MagicMock(name='Row2')
    row2.session_id = 'sess-2'
    row2.first_seen_at = datetime(2026, 5, 2, 9, 0, 0)
    row2.last_seen_at = datetime(2026, 5, 2, 9, 30, 0)
    row2.browser = 'Firefox'
    row2.browser_version = '118'
    row2.os = 'Linux'
    row2.device_type = 'desktop'
    row2.visits_count = 1

    session = MagicMock(name='SQLAlchemySession')
    session.scalar.return_value = 2
    result_proxy = MagicMock(name='ResultProxy')
    result_proxy.all.return_value = [row1, row2]
    session.execute.return_value = result_proxy
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(sessions_service, 'db_session', return_value=cm)

    # Act
    result = sessions_service.list(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        page=1,
        page_size=50,
        offset=0,
        device_type=None,
        browser=None,
    )

    # Assert
    assert result == {
        'items': [
            {
                'session_id': 'sess-1',
                'first_seen_at': '2026-05-01T10:00:00',
                'last_seen_at': '2026-05-01T11:00:00',
                'browser': 'Chrome',
                'browser_version': '120',
                'os': 'Windows',
                'device_type': 'desktop',
                'visits_count': 3,
            },
            {
                'session_id': 'sess-2',
                'first_seen_at': '2026-05-02T09:00:00',
                'last_seen_at': '2026-05-02T09:30:00',
                'browser': 'Firefox',
                'browser_version': '118',
                'os': 'Linux',
                'device_type': 'desktop',
                'visits_count': 1,
            },
        ],
        'page': 1,
        'page_size': 50,
        'total': 2,
        'has_more': False,
    }
