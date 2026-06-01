"""AC-17: admin.enable-user re-habilita un user existente -> 204.

Given un admin y un target existente (deleted_at None),
When se invoca admin.enable-user,
Then audita, habilita y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_admin_enable_user_ok(monkeypatch):
    """AC-17: target valido -> audit + enable + 204."""
    from controllers.admin import enable_user as ctl

    actor = _make_user(user_id='actor-id')
    target = _make_user(user_id='target-id', email='target@example.com')

    profile_svc = MagicMock()
    profile_svc.get_by_id.return_value = target
    audit_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'AuditAdminService', lambda _c: audit_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'user_id': '0193b8a0-0000-7000-8000-000000000018'},
    )
    result = ctl.EnableUser(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    assert audit_svc.log.call_count == 1
    profile_svc.enable.assert_called_once_with(user_id=target.id)
