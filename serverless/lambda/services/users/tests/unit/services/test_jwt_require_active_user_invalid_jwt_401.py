"""require_active_user — JWT invalido/revocado -> 401.

Given un access JWT que falla la verificacion (JwtError),
When se invoca require_active_user,
Then levanta ApplicationError con status_code 401.
"""

from unittest.mock import MagicMock

import pytest


def test_jwt_require_active_user_invalid_jwt_401(monkeypatch):
    from services import jwt_service
    from shared.auth.jwt import JwtError
    from shared.core.exceptions import ApplicationError

    fake_jwt = MagicMock()
    fake_jwt.verify.side_effect = JwtError('bad')
    monkeypatch.setattr(jwt_service, 'JwtService', lambda _c: fake_jwt)

    with pytest.raises(ApplicationError) as exc:
        jwt_service.require_active_user('Bearer abc', app_config=object())

    assert exc.value.status_code == 401
