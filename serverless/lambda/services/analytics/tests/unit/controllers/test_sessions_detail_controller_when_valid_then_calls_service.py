"""
Given un evento valido de sessions/detail con JWT y service mockeado,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con session_id y normaliza el shape (AC-12).
"""

import services.sessions_service as sessions_service
from controllers.sessions.detail import Detail


def test_sessions_detail_controller_when_valid_then_calls_service(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'session': {'session_id': 'sess-1'},
        'visits': [],
        'events_count': 0,
    }
    spy = mocker.patch.object(sessions_service, 'detail', return_value=expected)
    event = {
        'session_id': 'sess-1',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = Detail({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(session_id='sess-1')
