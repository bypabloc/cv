"""ProfileService.verify_password — sin credencial.

Given un user sin credencial password,
When se invoca verify_password,
Then devuelve False sin invocar el hasher.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_verify_password_no_credential(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    fake_session.get.return_value = None
    calls = {'verify': 0}

    def fake_verify(_pw, _h):
        calls['verify'] += 1
        return True

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(profile_service, 'verify_password', fake_verify)

    svc = profile_service.ProfileService(app_config=object())
    result = svc.verify_password(user_id='user-1', password='pw')

    assert result is False
    assert calls['verify'] == 0
