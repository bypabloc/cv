"""ProfileService.verify_password — password correcta + llamada keyword.

Given un user con credencial cuyo hash matchea la password,
When se invoca verify_password,
Then devuelve True y la shared `verify_password` se invoca con argumentos
     KEYWORD (`password=`, `hashed=`).

Guard de regresion: la shared `verify_password` es keyword-only
(`def verify_password(*, password, hashed)`). El bug fijado llamaba
posicional (`verify_password(password, cred.password_hash)`) -> TypeError
en runtime. El mock de este test es keyword-only a proposito: una llamada
posicional lo haria fallar.
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

    # Mock keyword-only: replica la firma real `(*, password, hashed)`.
    # Una llamada posicional levantaria TypeError y haria fallar el test.
    fake_verify = MagicMock(return_value=True)

    def _verify_kw_only(*, password, hashed):
        return fake_verify(password=password, hashed=hashed)

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service, 'verify_password', _verify_kw_only,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.verify_password(user_id='user-1', password='secret')

    assert result is True
    fake_verify.assert_called_once_with(
        password='secret', hashed='argon2-hash',
    )
