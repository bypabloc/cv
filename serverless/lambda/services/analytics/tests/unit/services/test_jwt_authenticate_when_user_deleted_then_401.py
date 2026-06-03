"""
Given un access JWT valido pero el user no existe o esta soft-deleted,
When se invoca authenticate,
Then levanta ApplicationError 401 USER_NOT_ACTIVE.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import services.jwt_service as jwt_service
from shared.core.exceptions import ApplicationError


@contextmanager
def _ctx(session):
    yield session


def test_jwt_authenticate_when_user_deleted_then_401(mocker):
    # Arrange
    claims = SimpleNamespace(sub=uuid4())
    mocker.patch.object(jwt_service, 'verify_jwt', return_value=claims)
    session = MagicMock()
    session.get.return_value = None
    mocker.patch.object(jwt_service, 'db_session', lambda: _ctx(session))
    app_config = mocker.Mock(
        jwt_secret='s', jwt_audience='portfolio', jwt_issuer='portfolio-auth'
    )

    # Act + Assert
    with pytest.raises(ApplicationError) as exc:
        jwt_service.authenticate('Bearer abc', app_config=app_config)

    assert exc.value.status_code == 401
    assert exc.value.code == 'USER_NOT_ACTIVE'
