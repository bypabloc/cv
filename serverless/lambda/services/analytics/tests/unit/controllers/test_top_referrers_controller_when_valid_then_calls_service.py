"""
Given un evento valido de analytics/top-referrers (limit),
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con date_from/date_to_exclusive/limit.
"""

from datetime import date

import services.analytics_service as analytics_service
from controllers.analytics.top_referrers import TopReferrers


def test_top_referrers_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'referrers': [],
        'utm_sources': [],
        'utm_mediums': [],
        'utm_campaigns': [],
    }
    spy = mocker.patch.object(
        analytics_service, 'top_referrers', return_value=expected
    )
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        'limit': 15,
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = TopReferrers({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28), limit=15
    )
