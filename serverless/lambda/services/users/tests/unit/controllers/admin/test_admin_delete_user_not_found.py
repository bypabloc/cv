"""AC-19: admin.delete-user de un target inexistente -> 404.

Given un admin y un target que no existe (get_by_id None) con sentinel valido,
When se invoca admin.delete-user,
Then devuelve 404 NOT_FOUND y NO hard-deletea.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user

_TARGET_ID = '0193b8a0-0000-7000-8000-000000000021'


def test_admin_delete_user_not_found(monkeypatch):
    """get_by_id None -> 404 NOT_FOUND sin hard_delete."""
    from controllers.admin import delete_user as ctl

    actor = _make_user(user_id='actor-id')

    profile_svc = MagicMock()
    profile_svc.get_by_id.return_value = None

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
            'user_id': _TARGET_ID,
            'confirm': f'HARD-DELETE-USER-{_TARGET_ID}',
        },
    )
    result = ctl.DeleteUser(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
    assert profile_svc.hard_delete.call_count == 0
