"""SessionService.get_family — devuelve el family_id de una sesion.

Given una sesion existente del user,
When se invoca get_family,
Then devuelve su family_id.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_session_get_family_returns_family_id(monkeypatch):
    from services import session_service

    fake_session = MagicMock()
    row = SimpleNamespace(family_id='fam-9')
    calls = {}

    def fake_get(_session, *, user_id, session_id):
        calls['user_id'] = user_id
        calls['session_id'] = session_id
        return row

    monkeypatch.setattr(
        session_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(session_service, 'get_session_by_id', fake_get)

    svc = session_service.SessionService(app_config=object())
    result = svc.get_family(user_id='user-1', session_id='sess-1')

    assert result == 'fam-9'
    assert calls['session_id'] == 'sess-1'
