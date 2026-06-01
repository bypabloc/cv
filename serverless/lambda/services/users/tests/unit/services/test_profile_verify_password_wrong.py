"""ProfileService.verify_password — password incorrecta.

Given un user con credencial cuyo hash NO matchea la password,
When se invoca verify_password,
Then devuelve False.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_verify_password_wrong(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    cred = MagicMock(password_hash='argon2-hash')
    fake_session.get.return_value = cred

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    # Mock keyword-only: replica la firma real `(*, password, hashed)`. Una
    # llamada posicional (el bug fijado) levantaria TypeError aqui.
    monkeypatch.setattr(
        profile_service,
        'verify_password',
        lambda *, password, hashed: False,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.verify_password(user_id='user-1', password='nope')

    assert result is False
