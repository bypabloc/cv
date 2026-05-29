"""AC-14: admin.get-user de un target inexistente -> 404.

Given un admin y un target que no existe (admin_detail None),
When se invoca admin.get-user,
Then devuelve 404 NOT_FOUND.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_admin_get_user_not_found(monkeypatch):
    """admin_detail None -> 404 NOT_FOUND."""
    from controllers.admin import get_user as ctl

    actor = _make_user(user_id='actor-id')

    profile_svc = MagicMock()
    profile_svc.admin_detail.return_value = None

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'user_id': '0193b8a0-0000-7000-8000-0000000000ff'},
    )
    result = ctl.GetUser(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
