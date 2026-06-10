"""require_active_user — JWT valido + no blacklisted + user activo.

Given un access JWT valido cuyo jti NO esta en la blacklist y un user
ACTIVE no borrado,
When se invoca require_active_user,
Then devuelve el AuthUser.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4


@contextmanager
def _ctx(session):
    yield session


def test_jwt_require_active_user_ok(monkeypatch):
    from services import jwt_service
    from shared.db.models.auth.enums import AuthUserStatus

    claims = SimpleNamespace(sub=uuid4(), jti=uuid4())
    monkeypatch.setattr(
        jwt_service, 'verify_jwt', lambda *_a, **_k: claims,
    )
    monkeypatch.setattr(
        jwt_service, '_is_blacklisted', lambda *_a, **_k: False,
    )
    active = MagicMock(deleted_at=None, status=AuthUserStatus.ACTIVE)
    fake_session = MagicMock()
    fake_session.get.return_value = active
    monkeypatch.setattr(
        jwt_service, 'db_session', lambda: _ctx(fake_session),
    )

    config = MagicMock(
        jwt_secret='s', jwt_issuer='i', jwt_audience='a',
    )
    result = jwt_service.require_active_user('Bearer abc', app_config=config)

    assert result is active
