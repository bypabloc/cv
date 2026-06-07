"""
Given un header Authorization,
When se invoca auth_guard.require_auth,
Then delega en jwt_service.require_active_user con el app_config del Lambda.
"""

import utils.auth_guard as auth_guard


def test_auth_guard_delegates_to_jwt_service(mocker):
    # Arrange
    spy = mocker.patch.object(
        auth_guard.jwt_service, 'require_active_user', return_value=None
    )

    # Act
    auth_guard.require_auth(authorization='Bearer abc')

    # Assert
    spy.assert_called_once_with('Bearer abc', app_config=auth_guard.app_config)
