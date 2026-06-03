"""
Given new=300, returning=200, total=500 de visitantes en el rango,
When se invoca analytics_service.retention (sin cache, via __wrapped__),
Then devuelve {new_visitors, returning_visitors, total, returning_rate}.
"""

from datetime import date
from unittest.mock import MagicMock

import services.analytics_service as analytics_service


def test_analytics_retention_when_data_then_returns_rates(mocker):
    # Arrange: el service hace s.execute(...).one() y lee los 3 campos.
    row = MagicMock()
    row.new_visitors = 300
    row.returning_visitors = 200
    row.total = 500
    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.one.return_value = row
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(analytics_service, 'db_session', return_value=cm)

    # Act
    result = analytics_service.retention.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )

    # Assert
    assert result == {
        'new_visitors': 300,
        'returning_visitors': 200,
        'total': 500,
        'returning_rate': 0.4,
    }
