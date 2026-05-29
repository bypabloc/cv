"""ProfileService.update — delega a update_profile con los campos.

Given un user_id y un subset de campos del perfil,
When se invoca update,
Then delega a update_profile y devuelve el AuthUser actualizado.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_update_delegates_to_repo(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    fake_user = MagicMock(id='user-1')
    calls = {}

    def fake_update(_session, *, user_id, **fields):
        calls['user_id'] = user_id
        calls['fields'] = fields
        return fake_user

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(profile_service, 'update_profile', fake_update)

    svc = profile_service.ProfileService(app_config=object())
    result = svc.update(user_id='user-1', display_name='Neo')

    assert result is fake_user
    assert calls['user_id'] == 'user-1'
    assert calls['fields'] == {'display_name': 'Neo'}
