"""AC-15: admin.disable-user de un target inexistente -> 404.

Given un admin y un target que no existe (get_by_id None),
When se invoca admin.disable-user,
Then devuelve 404 NOT_FOUND y NO deshabilita.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_admin_disable_user_not_found(monkeypatch):
    """get_by_id None -> 404 NOT_FOUND sin disable."""
    from controllers.admin import disable_user as ctl

    actor = _make_user(user_id='actor-id')

    profile_svc = MagicMock()
    profile_svc.get_by_id.return_value = None

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'AuditAdminService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'user_id': '0193b8a0-0000-7000-8000-000000000017'},
    )
    result = ctl.DisableUser(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
    assert profile_svc.disable.call_count == 0
