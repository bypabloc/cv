"""ProfileService.get_by_id — happy path.

Given un user existente en Neon,
When se invoca get_by_id con su user_id,
Then devuelve el AuthUser que retorna el repo get_user_by_id.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_get_by_id_returns_user(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    fake_user = MagicMock(id='user-1')
    calls = {}

    def fake_get(_session, *, user_id):
        calls['user_id'] = user_id
        return fake_user

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(profile_service, 'get_user_by_id', fake_get)

    svc = profile_service.ProfileService(app_config=object())
    result = svc.get_by_id(user_id='user-1')

    assert result is fake_user
    assert calls['user_id'] == 'user-1'
