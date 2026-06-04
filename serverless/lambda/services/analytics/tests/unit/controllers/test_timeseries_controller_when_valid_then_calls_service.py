"""
Given un evento valido de analytics/timeseries (bucket=week, niche, event_type),
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con date_from/date_to_exclusive/bucket/niche/event_type.
"""

from datetime import UTC, datetime

import services.analytics_service as analytics_service
from controllers.analytics.timeseries import Timeseries


def test_timeseries_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {'bucket': 'week', 'points': []}
    spy = mocker.patch.object(
        analytics_service, 'timeseries', return_value=expected
    )
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        'bucket': 'week',
        'niche': 'fintech',
        'event_type': 'page_view',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = Timeseries({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=datetime(2026, 4, 27, tzinfo=UTC),
        date_to=datetime(2026, 5, 28, tzinfo=UTC),
        bucket='week',
        niche='fintech',
        event_type='page_view',
    )
