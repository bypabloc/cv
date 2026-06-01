"""ProfileService.disable — delega a disable_user.

Given un user activo,
When se invoca disable,
Then delega a disable_user y devuelve True.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_disable_delegates_to_repo(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    calls = {}

    def fake_disable(_session, *, user_id):
        calls['user_id'] = user_id
        return True

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(profile_service, 'disable_user', fake_disable)

    svc = profile_service.ProfileService(app_config=object())
    result = svc.disable(user_id='user-1')

    assert result is True
    assert calls['user_id'] == 'user-1'
