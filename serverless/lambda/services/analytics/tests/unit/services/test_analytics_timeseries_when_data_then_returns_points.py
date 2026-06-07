"""
Given 2 buckets de eventos en el rango (bucket=day),
When se invoca analytics_service.timeseries (sin cache, via __wrapped__),
Then devuelve {bucket, points, from, to, filters} con los timestamps en isoformat.
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import services.analytics_service as analytics_service


def test_analytics_timeseries_when_data_then_returns_points(mocker):
    # Arrange: 2 rows (ts, count). row.ts es un datetime (isoformat).
    row1 = MagicMock()
    row1.ts = datetime(2026, 4, 27, tzinfo=UTC)
    row1.count = 12
    row2 = MagicMock()
    row2.ts = datetime(2026, 4, 28, tzinfo=UTC)
    row2.count = 7
    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.return_value = [row1, row2]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(analytics_service, 'db_session', return_value=cm)

    # Act
    result = analytics_service.timeseries.__wrapped__(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        bucket='day',
        niche=None,
        event_type=None,
    )

    # Assert
    assert result == {
        'bucket': 'day',
        'points': [
            {'timestamp': '2026-04-27T00:00:00+00:00', 'count': 12},
            {'timestamp': '2026-04-28T00:00:00+00:00', 'count': 7},
        ],
        'from': '2026-04-27',
        'to': '2026-05-28',
        'filters': {'niche': None, 'event_type': None},
    }
