"""
Given un evento valido de analytics/retention con JWT y service mockeado,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con date_from/date_to_exclusive y normaliza el shape.
"""

from datetime import date

import services.analytics_service as analytics_service
from controllers.analytics.retention import Retention


def test_retention_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'new_visitors': 30,
        'returning_visitors': 20,
        'total': 50,
        'returning_rate': 0.4,
    }
    spy = mocker.patch.object(
        analytics_service, 'retention', return_value=expected
    )
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = Retention({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )
