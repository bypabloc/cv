"""
Given un evento valido de sessions/list con JWT y service mockeado,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con rango + paginacion + filtros y normaliza el shape.
"""

from datetime import UTC, datetime

import services.sessions_service as sessions_service
from controllers.sessions.list import List


def test_sessions_list_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'items': [],
        'page': 2,
        'page_size': 25,
        'total': 0,
        'has_more': False,
    }
    spy = mocker.patch.object(sessions_service, 'list', return_value=expected)
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        'page': '2',
        'page_size': '25',
        'device_type': 'mobile',
        'browser': 'Safari',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = List({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=datetime(2026, 4, 27, tzinfo=UTC),
        date_to=datetime(2026, 5, 28, tzinfo=UTC),
        page=2,
        page_size=25,
        offset=25,
        device_type='mobile',
        browser='Safari',
    )
