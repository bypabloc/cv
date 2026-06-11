"""require_active_user con JWT invalido -> 401 TOKEN_INVALID.

Given verify_jwt levanta JwtError,
When se invoca require_active_user,
Then ApplicationError 401 TOKEN_INVALID.
"""

from unittest.mock import MagicMock

import pytest
from shared.core.exceptions import ApplicationError


def test_jwt_invalid_token_401(monkeypatch):
    from services import jwt_service
    from shared.auth.jwt import JwtError

    def _boom(*_a, **_k):
        raise JwtError('bad token')

    monkeypatch.setattr(jwt_service, 'verify_jwt', _boom)

    config = MagicMock(jwt_secret='s', jwt_issuer='i', jwt_audience='a')
    with pytest.raises(ApplicationError) as exc:
        jwt_service.require_active_user('Bearer bad', app_config=config)

    assert exc.value.status_code == 401
    assert exc.value.code == 'TOKEN_INVALID'
