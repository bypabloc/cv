"""_password_check helper — get_password_hash + check_password.

Cubre: user sin credentials -> None / False; password correcta -> True;
NeedsRehashError -> True (rehash es optimizacion, no afecta el login).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


def _fake_session_with(cred):
    @contextmanager
    def _cm():
        session = MagicMock()
        session.get.return_value = cred
        yield session

    return _cm


def test_get_password_hash_none_when_no_credentials(monkeypatch):
    from controllers.login import _password_check

    monkeypatch.setattr(
        _password_check,
        'db_session',
        _fake_session_with(None),
    )
    assert _password_check.get_password_hash(user_id='u-1') is None


def test_check_password_false_when_no_credentials(monkeypatch):
    from controllers.login import _password_check

    monkeypatch.setattr(
        _password_check,
        'db_session',
        _fake_session_with(None),
    )
    assert _password_check.check_password(user_id='u-1', password='x') is False


def test_check_password_true_when_matches(monkeypatch):
    from controllers.login import _password_check

    cred = MagicMock()
    cred.password_hash = '$argon2id$fake'
    monkeypatch.setattr(
        _password_check,
        'db_session',
        _fake_session_with(cred),
    )
    monkeypatch.setattr(
        _password_check,
        'verify_password',
        lambda *, password, hashed: True,
    )
    assert (
        _password_check.check_password(
            user_id='u-1',
            password='right',
        )
        is True
    )


def test_check_password_true_when_needs_rehash(monkeypatch):
    from controllers.login import _password_check
    from shared.auth.password import NeedsRehashError

    cred = MagicMock()
    cred.password_hash = '$argon2id$old'
    monkeypatch.setattr(
        _password_check,
        'db_session',
        _fake_session_with(cred),
    )

    def fake_verify(*, password, hashed):
        raise NeedsRehashError('old params')

    monkeypatch.setattr(_password_check, 'verify_password', fake_verify)
    assert (
        _password_check.check_password(
            user_id='u-1',
            password='right',
        )
        is True
    )
