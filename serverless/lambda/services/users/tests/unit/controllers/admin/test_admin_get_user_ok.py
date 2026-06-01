"""AC-14: admin.get-user devuelve el detalle del target -> 200.

Given un admin y un target existente,
When se invoca admin.get-user,
Then devuelve 200 con el dict de admin_detail.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_admin_get_user_ok(monkeypatch):
    """AC-14: admin_detail dict -> 200 con ese detalle."""
    from controllers.admin import get_user as ctl

    actor = _make_user(user_id='actor-id')
    detail = {
        'id': 'target-id',
        'email': 'target@example.com',
        'status': 'active',
        'mfa_configured': True,
        'session_count': 2,
    }

    profile_svc = MagicMock()
    profile_svc.admin_detail.return_value = detail

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'user_id': '0193b8a0-0000-7000-8000-000000000014'},
    )
    result = ctl.GetUser(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == detail
    profile_svc.admin_detail.assert_called_once_with(
        user_id='0193b8a0-0000-7000-8000-000000000014',
    )
