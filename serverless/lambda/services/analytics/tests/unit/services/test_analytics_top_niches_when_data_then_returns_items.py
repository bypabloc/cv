"""
Given 2 niches con sus visitas en el rango,
When se invoca analytics_service.top_niches (sin cache, via __wrapped__),
Then devuelve {items:[{niche, visits, unique_visitors}]}.
"""

from datetime import date
from unittest.mock import MagicMock

import services.analytics_service as analytics_service


def test_analytics_top_niches_when_data_then_returns_items(mocker):
    # Arrange
    row1 = MagicMock()
    row1.niche = 'fintech'
    row1.visits = 400
    row1.unique_visitors = 250
    row2 = MagicMock()
    row2.niche = '(none)'
    row2.visits = 150
    row2.unique_visitors = 100
    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.return_value = [row1, row2]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(analytics_service, 'db_session', return_value=cm)

    # Act
    result = analytics_service.top_niches.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28), limit=10
    )

    # Assert
    assert result == {
        'items': [
            {'niche': 'fintech', 'visits': 400, 'unique_visitors': 250},
            {'niche': '(none)', 'visits': 150, 'unique_visitors': 100},
        ]
    }
