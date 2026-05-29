"""SessionService.revoke_session — devuelve el family_id borrado.

Given una sesion existente del user,
When se invoca revoke_session,
Then delega a revoke_session del repo y devuelve su family_id.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_session_revoke_session_returns_family(monkeypatch):
    from services import session_service

    fake_session = MagicMock()
    calls = {}

    def fake_revoke(_session, *, user_id, session_id):
        calls['user_id'] = user_id
        calls['session_id'] = session_id
        return 'fam-7'

    monkeypatch.setattr(
        session_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(session_service, 'revoke_session', fake_revoke)

    svc = session_service.SessionService(app_config=object())
    result = svc.revoke_session(user_id='user-1', session_id='sess-1')

    assert result == 'fam-7'
    assert calls['session_id'] == 'sess-1'
