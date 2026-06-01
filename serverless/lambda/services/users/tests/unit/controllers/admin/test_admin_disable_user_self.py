"""AC-15: admin.disable-user sobre el propio actor -> 400.

Given un admin cuyo target es el mismo actor (mismo id),
When se invoca admin.disable-user,
Then devuelve 400 CANNOT_DISABLE_SELF y NO deshabilita.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_admin_disable_user_self(monkeypatch):
    """target.id == actor.id -> 400 CANNOT_DISABLE_SELF sin disable."""
    from controllers.admin import disable_user as ctl

    actor = _make_user(user_id='same-id')
    target = _make_user(user_id='same-id', email='admin@example.com')

    profile_svc = MagicMock()
    profile_svc.get_by_id.return_value = target

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'AuditAdminService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'user_id': '0193b8a0-0000-7000-8000-000000000016'},
    )
    result = ctl.DisableUser(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 400
    assert result['data']['error'] == 'CANNOT_DISABLE_SELF'
    assert profile_svc.disable.call_count == 0
