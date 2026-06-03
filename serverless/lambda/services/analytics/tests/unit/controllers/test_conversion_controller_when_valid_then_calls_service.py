"""
Given un evento valido de funnel/conversion con JWT y service mockeado,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con date_from/date_to_exclusive y normaliza el shape.
"""

from datetime import date

import services.funnel_service as funnel_service
from controllers.funnel.conversion import Conversion


def test_conversion_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {'sessions': 10, 'visits': 8, 'contacts': 1}
    spy = mocker.patch.object(
        funnel_service, 'conversion', return_value=expected
    )
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = Conversion({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )
