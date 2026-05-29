"""UserService — happy + sad path.

Mocks `db_session` y los helpers de `shared.db.repositories.auth` para
aislar el service del DB real.
"""

from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_get_by_email_returns_user_when_found(monkeypatch):
    from services import user_service

    fake_user = MagicMock(id='user-1', email='visitor@example.com')

    monkeypatch.setattr(user_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        user_service,
        'get_user_by_email',
        lambda _s, _e: fake_user,
    )

    svc = user_service.UserService(app_config=object())
    result = svc.get_by_email('Visitor@Example.com')

    assert result is fake_user


def test_create_pending_delegates_to_repo(monkeypatch):
    from services import user_service

    fake_user = MagicMock(id='user-new', email='new@example.com')
    calls = {}

    def fake_create(_session, *, email):
        calls['email'] = email
        return fake_user

    monkeypatch.setattr(user_service, 'db_session', _fake_session)
    monkeypatch.setattr(user_service, 'create_pending_user', fake_create)

    svc = user_service.UserService(app_config=object())
    result = svc.create_pending(email='  NEW@example.com  ')

    assert result is fake_user
    assert calls['email'] == 'new@example.com'


def test_mark_active_delegates_to_repo(monkeypatch):
    from services import user_service

    called = {}
    monkeypatch.setattr(user_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        user_service,
        'mark_user_active',
        lambda _s, u: called.setdefault('user', u),
    )

    svc = user_service.UserService(app_config=object())
    user = MagicMock(id='u')
    svc.mark_active(user)

    assert called['user'] is user


def test_reset_failed_attempts_delegates_to_repo(monkeypatch):
    from services import user_service

    called = {}
    monkeypatch.setattr(user_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        user_service,
        'reset_failed_attempts',
        lambda _s, u: called.setdefault('user', u),
    )

    svc = user_service.UserService(app_config=object())
    user = MagicMock(id='u')
    svc.reset_failed_attempts(user)

    assert called['user'] is user


def test_lock_user_delegates_to_repo(monkeypatch):
    from services import user_service

    called = {}
    monkeypatch.setattr(user_service, 'db_session', _fake_session)

    def _fake_lock(_session, _user, *, until):
        called['until'] = until

    monkeypatch.setattr(user_service, 'lock_user', _fake_lock)

    svc = user_service.UserService(app_config=object())
    until = datetime.now(tz=UTC)
    svc.lock_user(MagicMock(id='u'), until=until)

    assert called['until'] == until


def test_increment_failed_attempts_locks_at_fifth_failure(monkeypatch):
    from services import user_service

    calls = {'lock_called_with': None}

    monkeypatch.setattr(user_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        user_service,
        'increment_failed_attempts',
        lambda _s, _u: 5,
    )

    def fake_lock(_session, _user, *, until):
        calls['lock_called_with'] = until

    monkeypatch.setattr(user_service, 'lock_user', fake_lock)

    svc = user_service.UserService(app_config=object())
    user = MagicMock(id='user-x', failed_attempts=4)

    attempts = svc.increment_failed_attempts(user)

    assert attempts == 5
    assert calls['lock_called_with'] is not None
    assert calls['lock_called_with'] > datetime.now(tz=UTC)
