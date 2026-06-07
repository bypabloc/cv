"""
Given un evento valido de analytics/dashboard con JWT y service mockeado,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con date_from/date_to_exclusive/bucket/limit y
normaliza el shape.
"""

from datetime import UTC, datetime

import services.analytics_service as analytics_service
from controllers.analytics.dashboard import Dashboard


def test_dashboard_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'overview': {'sessions': 10},
        'timeseries': {'points': []},
        'top_pages': {'items': []},
        'top_referrers': {'referrers': []},
        'top_niches': {'items': []},
        'active_now': {'active_sessions': 2},
        'retention': {'total': 0},
    }
    spy = mocker.patch.object(
        analytics_service, 'dashboard', return_value=expected
    )
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        'bucket': 'day',
        'limit': '10',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = Dashboard({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=datetime(2026, 4, 27, tzinfo=UTC),
        date_to=datetime(2026, 5, 28, tzinfo=UTC),
        bucket='day',
        limit=10,
    )
