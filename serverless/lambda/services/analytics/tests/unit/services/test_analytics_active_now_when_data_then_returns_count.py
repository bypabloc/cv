"""
Given 23 sesiones con last_seen_at en los ultimos 5 min,
When se invoca analytics_service.active_now (sin cache, via __wrapped__) con
    el reloj fijado,
Then devuelve {active_sessions, threshold_minutes, as_of} determinista.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import services.analytics_service as analytics_service


def test_analytics_active_now_when_data_then_returns_count(mocker):
    # Arrange: fijar el reloj para que as_of sea determinista.
    fixed_now = datetime(2026, 5, 28, 12, 0, 0, tzinfo=UTC)
    fake_datetime = MagicMock(wraps=datetime)
    fake_datetime.now.return_value = fixed_now
    mocker.patch.object(analytics_service, 'datetime', fake_datetime)

    session = MagicMock(name='SQLAlchemySession')
    session.scalar.return_value = 23
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(analytics_service, 'db_session', return_value=cm)

    # Act
    result = analytics_service.active_now.__wrapped__()

    # Assert
    assert result == {
        'active_sessions': 23,
        'threshold_minutes': 5,
        'as_of': '2026-05-28T12:00:00+00:00',
    }
