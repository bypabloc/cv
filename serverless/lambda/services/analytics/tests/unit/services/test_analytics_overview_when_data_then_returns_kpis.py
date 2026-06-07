"""
Given counts y avg_duration en el rango,
When se invoca analytics_service.overview (sin cache, via __wrapped__),
Then devuelve los 7 KPIs + el rango (from/to) en isoformat.
"""

from datetime import date
from unittest.mock import MagicMock

import services.analytics_service as analytics_service


def test_analytics_overview_when_data_then_returns_kpis(mocker):
    # Arrange: 8 scalars en orden (sessions, visits, events, contacts,
    # unique_visitors, avg_duration, bounce_visits).
    session = MagicMock(name='SQLAlchemySession')
    session.scalar.side_effect = [1000, 800, 5000, 40, 600, 120.0, 200]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(analytics_service, 'db_session', return_value=cm)

    # Act
    result = analytics_service.overview.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )

    # Assert
    assert result == {
        'sessions': 1000,
        'visits': 800,
        'events': 5000,
        'contacts': 40,
        'unique_visitors': 600,
        'avg_visit_duration_sec': 120.0,
        'bounce_rate': 0.25,
        'from': '2026-04-27',
        'to': '2026-05-28',
    }
