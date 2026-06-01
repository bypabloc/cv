"""AC-6: delete-account de un user no-admin -> 204 soft-delete.

Given un user no-admin con el sentinel correcto,
When se invoca profile.delete-account,
Then soft-deletea, revoca las families de refresh y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_delete_account_ok(monkeypatch):
    """is_admin False + soft_delete retorna families -> 204 + revoke."""
    from controllers.profile import delete_account as ctl

    user = _make_user(email='visitor@example.com')

    profile_svc = MagicMock()
    profile_svc.soft_delete.return_value = ['fam']
    jwt_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'is_admin', lambda _e: False)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'confirm': 'DELETE-MY-ACCOUNT'})
    result = ctl.DeleteAccount(event=event).run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    profile_svc.soft_delete.assert_called_once_with(user_id=user.id)
    jwt_svc.revoke_families.assert_called_once_with(
        family_ids=['fam'],
        user_id=user.id,
    )
