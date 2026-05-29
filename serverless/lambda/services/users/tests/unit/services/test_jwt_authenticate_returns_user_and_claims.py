"""authenticate — JWT valido + user activo devuelve (user, claims).

Given un access JWT valido y un user ACTIVE no borrado,
When se invoca authenticate,
Then devuelve la tupla (AuthUser, JwtClaims).
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4


@contextmanager
def _ctx(session):
    yield session


def test_jwt_authenticate_returns_user_and_claims(monkeypatch):
    from services import jwt_service
    from shared.db.models import AuthUserStatus

    claims = SimpleNamespace(sub=uuid4(), family_id='fam-1')
    fake_jwt = MagicMock()
    fake_jwt.verify.return_value = claims
    monkeypatch.setattr(jwt_service, 'JwtService', lambda _c: fake_jwt)

    active = MagicMock(deleted_at=None, status=AuthUserStatus.ACTIVE)
    fake_session = MagicMock()
    fake_session.get.return_value = active
    monkeypatch.setattr(
        jwt_service, 'db_session', lambda: _ctx(fake_session),
    )

    user, result_claims = jwt_service.authenticate(
        'Bearer abc', app_config=object(),
    )

    assert user is active
    assert result_claims is claims
