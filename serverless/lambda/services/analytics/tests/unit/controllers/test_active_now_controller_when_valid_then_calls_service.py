"""
Given un evento valido de analytics/active-now (SIN rango de fechas),
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service SIN kwargs y normaliza el shape.
"""

import services.analytics_service as analytics_service
from controllers.analytics.active_now import ActiveNow


def test_active_now_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'active_sessions': 5,
        'threshold_minutes': 5,
        'as_of': '2026-05-28T12:00:00+00:00',
    }
    spy = mocker.patch.object(
        analytics_service, 'active_now', return_value=expected
    )
    event = {'_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'}}
    controller = ActiveNow({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with()
