"""SessionService.list_for_user — marca la sesion actual por family.

Given dos sesiones del user, una con el family_id del access JWT en curso,
When se invoca list_for_user con current_family_id,
Then esa sesion sale con current=True y la otra con current=False.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def _row(*, sid, family_id):
    return SimpleNamespace(
        id=sid,
        device_info={'os': 'linux'},
        ip='1.1.1.1',
        country='CL',
        family_id=family_id,
        created_at=SimpleNamespace(isoformat=lambda: '2026-01-01T00:00:00'),
        last_active_at=SimpleNamespace(
            isoformat=lambda: '2026-01-02T00:00:00',
        ),
    )


def test_session_list_for_user_marks_current(monkeypatch):
    from services import session_service

    fake_session = MagicMock()
    rows = [
        _row(sid='sess-cur', family_id='fam-cur'),
        _row(sid='sess-old', family_id='fam-old'),
    ]

    monkeypatch.setattr(
        session_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        session_service, 'list_user_sessions', lambda _s, *, user_id: rows,
    )

    svc = session_service.SessionService(app_config=object())
    result = svc.list_for_user(
        user_id='user-1', current_family_id='fam-cur',
    )

    assert result == [
        {
            'session_id': 'sess-cur',
            'device_info': {'os': 'linux'},
            'ip': '1.1.1.1',
            'country': 'CL',
            'created_at': '2026-01-01T00:00:00',
            'last_active_at': '2026-01-02T00:00:00',
            'current': True,
        },
        {
            'session_id': 'sess-old',
            'device_info': {'os': 'linux'},
            'ip': '1.1.1.1',
            'country': 'CL',
            'created_at': '2026-01-01T00:00:00',
            'last_active_at': '2026-01-02T00:00:00',
            'current': False,
        },
    ]
