"""ProfileService.verify_password — password correcta.

Given un user con credencial cuyo hash matchea la password,
When se invoca verify_password,
Then devuelve True.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_verify_password_ok(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    cred = MagicMock(password_hash='argon2-hash')
    fake_session.get.return_value = cred

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service, 'verify_password', lambda _pw, _h: True,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.verify_password(user_id='user-1', password='secret')

    assert result is True
