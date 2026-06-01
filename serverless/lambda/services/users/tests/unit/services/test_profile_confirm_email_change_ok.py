"""ProfileService.confirm_email_change — link valido + email libre.

Given un magic-link valido cuyo new_email sigue libre,
When se invoca confirm_email_change,
Then actualiza el email y devuelve (user_id, old_email, new_email).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_confirm_email_change_ok(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    link = MagicMock(
        user_id='user-1',
        meta_data={'new_email': 'new@example.com'},
    )
    user = MagicMock(id='user-1', email='old@example.com')
    calls = {}

    def fake_update(_session, *, user_id, new_email):
        calls['user_id'] = user_id
        calls['new_email'] = new_email

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(profile_service, 'hash_token', lambda _t: 'h')
    monkeypatch.setattr(
        profile_service,
        'consume_email_change_link',
        lambda _s, *, token_hash: link,
    )
    monkeypatch.setattr(
        profile_service, 'get_user_by_email', lambda _s, _e: None,
    )
    monkeypatch.setattr(
        profile_service, 'get_user_by_id', lambda _s, *, user_id: user,
    )
    monkeypatch.setattr(profile_service, 'update_user_email', fake_update)

    svc = profile_service.ProfileService(app_config=object())
    result = svc.confirm_email_change(token='tok')

    assert result == ('user-1', 'old@example.com', 'new@example.com')
    assert calls['new_email'] == 'new@example.com'
