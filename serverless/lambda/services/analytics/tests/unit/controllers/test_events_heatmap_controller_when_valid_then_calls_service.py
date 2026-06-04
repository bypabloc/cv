"""
Given un evento valido de events/heatmap con JWT y service mockeado,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con date_from/date_to_exclusive y normaliza el shape.
"""

from datetime import UTC, datetime

import services.events_service as events_service
from controllers.events.heatmap import Heatmap


def test_events_heatmap_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {'cells': [{'dow': 1, 'hour': 9, 'count': 3}]}
    spy = mocker.patch.object(events_service, 'heatmap', return_value=expected)
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = Heatmap({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=datetime(2026, 4, 27, tzinfo=UTC),
        date_to=datetime(2026, 5, 28, tzinfo=UTC),
    )
