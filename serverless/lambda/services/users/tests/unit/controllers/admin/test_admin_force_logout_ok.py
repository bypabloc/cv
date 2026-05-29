"""AC-18: admin.force-logout cierra todas las sesiones del target -> 204.

Given un admin y un target existente con 2 families activas,
When se invoca admin.force-logout,
Then revoca todas las sesiones, blacklistea cada family y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_admin_force_logout_ok(monkeypatch):
    """AC-18: revoke_all_for_user + revoke_families + 204."""
    from controllers.admin import force_logout as ctl

    actor = _make_user(user_id='actor-id')
    target = _make_user(user_id='target-id', email='target@example.com')

    profile_svc = MagicMock()
    profile_svc.get_by_id.return_value = target
    session_svc = MagicMock()
    session_svc.revoke_all_for_user.return_value = ['f1', 'f2']
    jwt_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'SessionService', lambda _c: session_svc)
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(ctl, 'AuditAdminService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'user_id': '0193b8a0-0000-7000-8000-000000000019'},
    )
    result = ctl.ForceLogout(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    session_svc.revoke_all_for_user.assert_called_once_with(
        user_id=target.id,
    )
    jwt_svc.revoke_families.assert_called_once_with(
        family_ids=['f1', 'f2'], user_id=target.id,
    )
