"""SessionService.revoke_all_for_user — devuelve todas las families.

Given un user con varias sesiones,
When se invoca revoke_all_for_user,
Then delega a revoke_all_user_sessions y devuelve la lista de family_id.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_session_revoke_all_returns_families(monkeypatch):
    from services import session_service

    fake_session = MagicMock()
    calls = {}

    def fake_revoke_all(_session, *, user_id):
        calls['user_id'] = user_id
        return ['fam-1', 'fam-2', 'fam-3']

    monkeypatch.setattr(
        session_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        session_service, 'revoke_all_user_sessions', fake_revoke_all,
    )

    svc = session_service.SessionService(app_config=object())
    result = svc.revoke_all_for_user(user_id='user-1')

    assert result == ['fam-1', 'fam-2', 'fam-3']
    assert calls['user_id'] == 'user-1'
