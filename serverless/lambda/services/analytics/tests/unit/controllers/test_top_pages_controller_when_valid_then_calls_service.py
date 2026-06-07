"""
Given un evento valido de analytics/top-pages (limit, niche),
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con date_from/date_to_exclusive/limit/niche.
"""

from datetime import UTC, datetime

import services.analytics_service as analytics_service
from controllers.analytics.top_pages import TopPages


def test_top_pages_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {'items': []}
    spy = mocker.patch.object(
        analytics_service, 'top_pages', return_value=expected
    )
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        'limit': 5,
        'niche': 'architect',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = TopPages({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=datetime(2026, 4, 27, tzinfo=UTC),
        date_to=datetime(2026, 5, 28, tzinfo=UTC),
        limit=5,
        niche='architect',
    )
