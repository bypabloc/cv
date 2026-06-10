"""require_active_user con jti blacklisted -> 401 TOKEN_INVALID.

Given un JWT con firma valida pero jti presente en la blacklist DDB,
When se invoca require_active_user,
Then ApplicationError 401 TOKEN_INVALID (el JwtRevokedError interno es
una subclase de JwtError).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from shared.core.exceptions import ApplicationError


def test_jwt_blacklisted_401(monkeypatch):
    from services import jwt_service

    claims = SimpleNamespace(sub=uuid4(), jti=uuid4())
    monkeypatch.setattr(
        jwt_service, 'verify_jwt', lambda *_a, **_k: claims,
    )
    monkeypatch.setattr(
        jwt_service, '_is_blacklisted', lambda *_a, **_k: True,
    )

    config = MagicMock(jwt_secret='s', jwt_issuer='i', jwt_audience='a')
    with pytest.raises(ApplicationError) as exc:
        jwt_service.require_active_user('Bearer abc', app_config=config)

    assert exc.value.status_code == 401
    assert exc.value.code == 'TOKEN_INVALID'
