"""mfa.enable de un metodo soft-disabled -> 204.

Given un metodo MFA soft-disabled del user,
When se invoca mfa.enable,
Then re-activa el metodo y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_enable_ok(monkeypatch):
    """service.enable -> True -> 204 + re-activa el metodo."""
    from controllers.mfa import enable as mfa_enable
    from shared.db.models.auth.enums import AuthMfaKind

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.enable.return_value = True

    monkeypatch.setattr(
        mfa_enable,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(mfa_enable, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(mfa_enable, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(mfa_enable, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'totp'})
    result = mfa_enable.Enable(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    assert result['data'] == {}
    mfa_svc.enable.assert_called_once_with(
        user_id=user.id,
        kind=AuthMfaKind.TOTP,
    )
