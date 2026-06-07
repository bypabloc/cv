"""
Given 2 page_path con sus counts en el rango,
When se invoca analytics_service.top_pages (sin cache, via __wrapped__),
Then devuelve {items:[{page_path, events, unique_visitors, unique_visits}]}.
"""

from datetime import date
from unittest.mock import MagicMock

import services.analytics_service as analytics_service


def test_analytics_top_pages_when_data_then_returns_items(mocker):
    # Arrange
    row1 = MagicMock()
    row1.page_path = '/'
    row1.events = 500
    row1.unique_visitors = 300
    row1.unique_visits = 350
    row2 = MagicMock()
    row2.page_path = '/projects'
    row2.events = 120
    row2.unique_visitors = 90
    row2.unique_visits = 100
    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.return_value = [row1, row2]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(analytics_service, 'db_session', return_value=cm)

    # Act
    result = analytics_service.top_pages.__wrapped__(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        limit=10,
        niche=None,
    )

    # Assert
    assert result == {
        'items': [
            {
                'page_path': '/',
                'events': 500,
                'unique_visitors': 300,
                'unique_visits': 350,
            },
            {
                'page_path': '/projects',
                'events': 120,
                'unique_visitors': 90,
                'unique_visits': 100,
            },
        ]
    }
