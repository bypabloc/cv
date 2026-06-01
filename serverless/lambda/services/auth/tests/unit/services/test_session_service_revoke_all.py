"""SessionService.revoke_all_for_user setea sessions_revoked_at = now().

Given un user en la sesion,
When se invoca revoke_all_for_user,
Then user.sessions_revoked_at queda seteado (no None).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


def test_session_service_revoke_all_sets_timestamp(monkeypatch):
    from services import session_service

    user = MagicMock()
    user.sessions_revoked_at = None

    @contextmanager
    def _fake_session():
        session = MagicMock()
        session.get.return_value = user
        yield session

    monkeypatch.setattr(session_service, 'db_session', _fake_session)

    svc = session_service.SessionService(app_config=object())
    svc.revoke_all_for_user(user_id='user-1')

    assert user.sessions_revoked_at is not None


def test_session_service_revoke_all_user_not_found(monkeypatch):
    from services import session_service

    @contextmanager
    def _fake_session():
        session = MagicMock()
        session.get.return_value = None
        yield session

    monkeypatch.setattr(session_service, 'db_session', _fake_session)

    svc = session_service.SessionService(app_config=object())
    # No debe lanzar si el user no existe.
    svc.revoke_all_for_user(user_id='ghost')
