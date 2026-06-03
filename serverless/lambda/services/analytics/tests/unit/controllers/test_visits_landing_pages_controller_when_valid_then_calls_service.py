"""
Given un evento valido de visits/landing-pages con rango, limit y JWT,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con el rango (to exclusivo) y el limit.
"""

from datetime import date

import services.visits_service as visits_service
from controllers.visits.landing_pages import LandingPages


def test_visits_landing_pages_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'items': [
            {'landing_page_path': '/', 'visits': 500, 'unique_visitors': 300},
        ]
    }
    spy = mocker.patch.object(
        visits_service, 'landing_pages', return_value=expected
    )
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        'limit': 10,
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = LandingPages({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        limit=10,
    )
