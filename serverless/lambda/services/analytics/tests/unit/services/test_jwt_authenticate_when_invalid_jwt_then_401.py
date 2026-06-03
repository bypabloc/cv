"""
Given un Bearer con un JWT invalido/expirado,
When se invoca authenticate,
Then levanta ApplicationError 401 TOKEN_INVALID (AC-24).
"""

import pytest
import services.jwt_service as jwt_service
from shared.auth.jwt import JwtInvalidError
from shared.core.exceptions import ApplicationError


def test_jwt_authenticate_when_invalid_jwt_then_401(mocker):
    # Arrange
    mocker.patch.object(
        jwt_service, 'verify_jwt', side_effect=JwtInvalidError('bad')
    )
    app_config = mocker.Mock(
        jwt_secret='s', jwt_audience='portfolio', jwt_issuer='portfolio-auth'
    )

    # Act + Assert
    with pytest.raises(ApplicationError) as exc:
        jwt_service.authenticate('Bearer not-a-real-jwt', app_config=app_config)

    assert exc.value.status_code == 401
    assert exc.value.code == 'TOKEN_INVALID'
