"""
Given 2 landing_page_path con sus counts en el rango,
When se invoca visits_service.landing_pages (cacheada, via __wrapped__),
Then devuelve {items:[{landing_page_path, visits, unique_visitors}]}.
"""

from datetime import date
from unittest.mock import MagicMock

import services.visits_service as visits_service


def test_visits_landing_pages_when_data_then_returns_items(mocker):
    # Arrange
    row1 = MagicMock()
    row1.landing_page_path = '/'
    row1.visits = 500
    row1.unique_visitors = 300
    row2 = MagicMock()
    row2.landing_page_path = '/projects'
    row2.visits = 120
    row2.unique_visitors = 90
    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.return_value = [row1, row2]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(visits_service, 'db_session', return_value=cm)

    # Act
    result = visits_service.landing_pages.__wrapped__(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        limit=10,
    )

    # Assert
    assert result == {
        'items': [
            {
                'landing_page_path': '/',
                'visits': 500,
                'unique_visitors': 300,
            },
            {
                'landing_page_path': '/projects',
                'visits': 120,
                'unique_visitors': 90,
            },
        ]
    }
