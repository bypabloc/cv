"""AC-29: delete-account de un admin -> 409 CANNOT_DELETE_ADMIN_ACCOUNT.

Given un user cuyo email esta en la whitelist admin,
When se invoca profile.delete-account,
Then devuelve 409 CANNOT_DELETE_ADMIN_ACCOUNT y NO ejecuta soft_delete.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_delete_account_admin_guard(monkeypatch):
    """is_admin True -> 409 CANNOT_DELETE_ADMIN_ACCOUNT + sin soft_delete."""
    from controllers.profile import delete_account as ctl

    user = _make_user(email='admin@example.com')

    profile_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'is_admin', lambda _e: True)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'confirm': 'DELETE-MY-ACCOUNT'})
    result = ctl.DeleteAccount(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 409
    assert result['data']['error'] == 'CANNOT_DELETE_ADMIN_ACCOUNT'
    assert profile_svc.soft_delete.call_count == 0
