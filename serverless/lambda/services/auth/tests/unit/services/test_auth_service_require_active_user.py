"""require_active_user — happy path + sad paths (header / JWT / user).

Cubre: header ausente -> 401, JWT invalido -> 401, user inactivo -> 401,
user activo -> devuelve el user.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest


@contextmanager
def _fake_session_returning(user):
    session = MagicMock()
    session.get.return_value = user
    yield session


def test_require_active_user_no_header_raises():
    from services.auth_service import require_active_user
    from shared.core.exceptions import ApplicationError

    with pytest.raises(ApplicationError) as exc:
        require_active_user(None, app_config=object())

    assert exc.value.status_code == 401


def test_require_active_user_invalid_jwt_raises(monkeypatch):
    from services import auth_service
    from shared.auth.jwt import JwtInvalidError
    from shared.core.exceptions import ApplicationError

    fake_jwt = MagicMock()
    fake_jwt.verify.side_effect = JwtInvalidError('bad')
    monkeypatch.setattr(auth_service, 'JwtService', lambda _c: fake_jwt)

    with pytest.raises(ApplicationError) as exc:
        auth_service.require_active_user(
            'Bearer abc',
            app_config=object(),
        )

    assert exc.value.status_code == 401


def test_require_active_user_inactive_raises(monkeypatch):
    from services import auth_service
    from shared.core.exceptions import ApplicationError
    from shared.db.models.auth.enums import AuthUserStatus

    claims = SimpleNamespace(sub=uuid4())
    fake_jwt = MagicMock()
    fake_jwt.verify.return_value = claims
    monkeypatch.setattr(auth_service, 'JwtService', lambda _c: fake_jwt)

    inactive = MagicMock()
    inactive.status = AuthUserStatus.DISABLED
    monkeypatch.setattr(
        auth_service,
        'db_session',
        lambda: _fake_session_returning(inactive),
    )

    with pytest.raises(ApplicationError) as exc:
        auth_service.require_active_user('Bearer abc', app_config=object())

    assert exc.value.status_code == 401


def test_require_active_user_active_returns_user(monkeypatch):
    from services import auth_service
    from shared.db.models.auth.enums import AuthUserStatus

    claims = SimpleNamespace(sub=uuid4())
    fake_jwt = MagicMock()
    fake_jwt.verify.return_value = claims
    monkeypatch.setattr(auth_service, 'JwtService', lambda _c: fake_jwt)

    active = MagicMock()
    active.status = AuthUserStatus.ACTIVE
    monkeypatch.setattr(
        auth_service,
        'db_session',
        lambda: _fake_session_returning(active),
    )

    result = auth_service.require_active_user(
        'Bearer abc',
        app_config=object(),
    )

    assert result is active
