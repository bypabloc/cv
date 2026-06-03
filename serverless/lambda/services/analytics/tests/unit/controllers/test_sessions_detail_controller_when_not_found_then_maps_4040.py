"""
Given un evento de sessions/detail cuyo service levanta NotFoundError,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then el _base mapea el error a {is_valid: False, code: 4040} (AC-11).
"""

import services.sessions_service as sessions_service
from controllers.sessions.detail import Detail
from services._errors import NotFoundError


def test_sessions_detail_controller_when_not_found_then_maps_4040(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange: el service levanta NotFoundError.
    spy = mocker.patch.object(
        sessions_service,
        'detail',
        side_effect=NotFoundError('session nope not found'),
    )
    event = {
        'session_id': 'nope',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = Detail({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'NOT_FOUND',
            'message': 'session nope not found',
        },
        'code': 4040,
    }
    spy.assert_called_once_with(session_id='nope')
