"""
Given un access JWT valido y un user ACTIVE no borrado,
When se invoca authenticate,
Then devuelve el AuthUser activo.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import services.jwt_service as jwt_service
from shared.db.models.auth.enums import AuthUserStatus


@contextmanager
def _ctx(session):
    yield session


def test_jwt_authenticate_when_active_user_then_returns_user(mocker):
    # Arrange
    claims = SimpleNamespace(sub=uuid4())
    mocker.patch.object(jwt_service, 'verify_jwt', return_value=claims)
    active = MagicMock(deleted_at=None, status=AuthUserStatus.ACTIVE)
    session = MagicMock()
    session.get.return_value = active
    mocker.patch.object(jwt_service, 'db_session', lambda: _ctx(session))
    app_config = mocker.Mock(
        jwt_secret='s', jwt_audience='portfolio', jwt_issuer='portfolio-auth'
    )

    # Act
    user = jwt_service.authenticate('Bearer abc', app_config=app_config)

    # Assert
    assert user is active
