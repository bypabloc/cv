"""
Given un access JWT valido pero el user esta LOCKED,
When se invoca authenticate,
Then levanta ApplicationError 403 ACCOUNT_LOCKED.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import services.jwt_service as jwt_service
from shared.core.exceptions import ApplicationError
from shared.db.models.auth.enums import AuthUserStatus


@contextmanager
def _ctx(session):
    yield session


def test_jwt_authenticate_when_locked_then_403(mocker):
    # Arrange
    claims = SimpleNamespace(sub=uuid4())
    mocker.patch.object(jwt_service, 'verify_jwt', return_value=claims)
    locked = MagicMock(deleted_at=None, status=AuthUserStatus.LOCKED)
    session = MagicMock()
    session.get.return_value = locked
    mocker.patch.object(jwt_service, 'db_session', lambda: _ctx(session))
    app_config = mocker.Mock(
        jwt_secret='s', jwt_audience='portfolio', jwt_issuer='portfolio-auth'
    )

    # Act + Assert
    with pytest.raises(ApplicationError) as exc:
        jwt_service.authenticate('Bearer abc', app_config=app_config)

    assert exc.value.status_code == 403
    assert exc.value.code == 'ACCOUNT_LOCKED'
