"""AC-19: admin.delete-user sobre el propio actor -> 400.

Given un admin cuyo target es el mismo actor (mismo id) con sentinel valido,
When se invoca admin.delete-user,
Then devuelve 400 CANNOT_DELETE_SELF y NO hard-deletea.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user

_SAME_ID = '0193b8a0-0000-7000-8000-000000000020'


def test_admin_delete_user_self(monkeypatch):
    """target.id == actor.id -> 400 CANNOT_DELETE_SELF sin hard_delete."""
    from controllers.admin import delete_user as ctl

    actor = _make_user(user_id='same-id')
    target = _make_user(user_id='same-id', email='admin@example.com')

    profile_svc = MagicMock()
    profile_svc.get_by_id.return_value = target

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'SessionService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'AuditAdminService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={
            'user_id': _SAME_ID,
            'confirm': f'HARD-DELETE-USER-{_SAME_ID}',
        },
    )
    result = ctl.DeleteUser(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 400
    assert result['data']['error'] == 'CANNOT_DELETE_SELF'
    assert profile_svc.hard_delete.call_count == 0
