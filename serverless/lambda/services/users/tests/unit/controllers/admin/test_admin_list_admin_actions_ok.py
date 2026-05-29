"""AC-20: admin.list-admin-actions devuelve el historico -> 200.

Given un admin y 2 admin actions con page_size 50,
When se invoca admin.list-admin-actions,
Then devuelve 200 con la lista de actions y next_cursor None
(len 2 < page_size 50).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_admin_list_admin_actions_ok(monkeypatch):
    """AC-20: list_actions -> 200 con esas actions y next_cursor None."""
    from controllers.admin import list_admin_actions as ctl

    actor = _make_user(user_id='actor-id')
    actions = [
        {'id': 'a1', 'action': 'disable', 'target_user_id': 't1'},
        {'id': 'a2', 'action': 'enable', 'target_user_id': 't2'},
    ]

    audit_svc = MagicMock()
    audit_svc.list_actions.return_value = actions

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'AuditAdminService', lambda _c: audit_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event()
    result = ctl.ListAdminActions(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['actions'] == actions
    assert result['data']['page_size'] == 50
    assert result['data']['total_returned'] == 2
    assert result['data']['next_cursor'] is None
