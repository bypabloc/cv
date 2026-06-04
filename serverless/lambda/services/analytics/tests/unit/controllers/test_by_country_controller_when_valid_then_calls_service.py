"""
Given un evento valido de geo/by-country (from, to, limit),
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con date_from/date_to_exclusive/limit.
"""

from datetime import UTC, datetime

import services.geo_service as geo_service
from controllers.geo.by_country import ByCountry


def test_by_country_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'items': [
            {'country': 'AR', 'sessions': 30, 'visits': 45, 'events': 200},
        ],
        'total': 30,
    }
    spy = mocker.patch.object(geo_service, 'by_country', return_value=expected)
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        'limit': 25,
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = ByCountry({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=datetime(2026, 4, 27, tzinfo=UTC),
        date_to=datetime(2026, 5, 28, tzinfo=UTC),
        limit=25,
    )
