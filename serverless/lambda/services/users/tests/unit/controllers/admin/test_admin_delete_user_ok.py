"""AC-19: admin.delete-user hard-deletea un target distinto al actor -> 204.

Given un admin, un target existente (id != actor) y el sentinel correcto,
When se invoca admin.delete-user,
Then audita, revoca families, notifica, hard-deletea y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user

_TARGET_ID = '0193b8a0-0000-7000-8000-000000000019'


def test_admin_delete_user_ok(monkeypatch):
    """AC-19: sentinel valido + target != actor -> 204 con cascada."""
    from controllers.admin import delete_user as ctl

    actor = _make_user(user_id='actor-id')
    target = _make_user(user_id='target-id', email='target@example.com')

    profile_svc = MagicMock()
    profile_svc.get_by_id.return_value = target
    session_svc = MagicMock()
    session_svc.revoke_all_for_user.return_value = ['f1']
    jwt_svc = MagicMock()
    email_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'SessionService', lambda _c: session_svc)
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(ctl, 'EmailDispatchService', lambda _c: email_svc)
    monkeypatch.setattr(ctl, 'AuditAdminService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={
            'user_id': _TARGET_ID,
            'confirm': f'HARD-DELETE-USER-{_TARGET_ID}',
        },
    )
    result = ctl.DeleteUser(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    profile_svc.hard_delete.assert_called_once_with(user_id=target.id)
    jwt_svc.revoke_families.assert_called_once_with(
        family_ids=['f1'], user_id=target.id,
    )
    email_svc.publish_account_deleted.assert_called_once_with(
        to=target.email, user_id=target.id, niche=None,
    )
