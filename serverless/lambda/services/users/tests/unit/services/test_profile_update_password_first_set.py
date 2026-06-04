"""ProfileService.update_password — primer set (user passwordless).

Given un user SIN credencial (cred is None) y current_password=None,
When se invoca update_password,
Then establece el primer password (set_password_hash) y devuelve True sin
  intentar verificar nada.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_update_password_sets_first_when_no_credential(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    fake_session.get.return_value = None  # passwordless: sin credencial

    set_calls = []
    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service,
        'set_password_hash',
        lambda session, *, user_id, password_hash: set_calls.append(user_id),
    )
    monkeypatch.setattr(
        profile_service, 'hash_password', lambda pw: f'hashed:{pw}',
    )
    verify_calls = []
    monkeypatch.setattr(
        profile_service,
        'verify_password',
        lambda **_k: verify_calls.append(True),
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.update_password(
        user_id='user-1',
        current_password=None,
        new_password='brand-new-pass-12',
    )

    assert result is True
    assert set_calls == ['user-1']
    assert verify_calls == []  # passwordless NO verifica nada
