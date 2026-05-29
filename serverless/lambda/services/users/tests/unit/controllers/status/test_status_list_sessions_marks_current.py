"""AC-8: status.list-sessions lista las sesiones y marca la actual -> 200.

Given un user con access JWT cuyo claims.family_id es 'fam-current',
When se invoca status.list-sessions,
Then devuelve 200 con las sesiones de list_for_user (current marcado por
el family_id en curso).
"""

from unittest.mock import MagicMock

from .._helpers import _make_access_claims, _make_authed_event, _make_user


def test_status_list_sessions_marks_current(monkeypatch):
    """AC-8: list-sessions -> 200, current_family_id viene del access JWT."""
    from controllers.status import list_sessions as ctl

    user = _make_user(user_id='0193b8a0-0000-7000-8000-000000000008')
    claims = _make_access_claims(family_id='fam-current')

    session_svc = MagicMock()
    session_svc.list_for_user.return_value = [
        {'session_id': 's1', 'family_id': 'fam-current', 'current': True},
        {'session_id': 's2', 'family_id': 'fam-other', 'current': False},
    ]

    monkeypatch.setattr(
        ctl, 'authenticate', lambda *_a, **_k: (user, claims),
    )
    monkeypatch.setattr(ctl, 'SessionService', lambda _c: session_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event()
    result = ctl.ListSessions(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['sessions'] == [
        {'session_id': 's1', 'family_id': 'fam-current', 'current': True},
        {'session_id': 's2', 'family_id': 'fam-other', 'current': False},
    ]
    session_svc.list_for_user.assert_called_once_with(
        user_id=user.id, current_family_id='fam-current',
    )
