"""ProfileService.create_email_change_link — genera token + ttl.

Given un user que pide cambiar su email,
When se invoca create_email_change_link,
Then genera el token plano, lo hashea, inserta el link y devuelve
(plain_token, 900).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_create_email_change_link_returns_plain_and_ttl(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    calls = {}

    def fake_insert(_session, *, user_id, token_hash, expires_at, new_email,
                    ip, user_agent):
        calls['user_id'] = user_id
        calls['token_hash'] = token_hash
        calls['new_email'] = new_email

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service, 'generate_opaque_token', lambda: 'plain-token',
    )
    monkeypatch.setattr(
        profile_service, 'hash_token', lambda _t: 'hashed-token',
    )
    monkeypatch.setattr(
        profile_service, 'insert_email_change_link', fake_insert,
    )

    svc = profile_service.ProfileService(app_config=object())
    plain, ttl = svc.create_email_change_link(
        user_id='user-1', new_email='new@example.com',
    )

    assert plain == 'plain-token'
    assert ttl == 900
    assert calls['token_hash'] == 'hashed-token'
    assert calls['new_email'] == 'new@example.com'
