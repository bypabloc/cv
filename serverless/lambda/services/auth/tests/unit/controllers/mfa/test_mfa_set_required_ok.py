"""mfa.set-required(required=True) -> 204.

Given un metodo MFA activo del user,
When se invoca mfa.set-required con required=True,
Then actualiza el flag y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_set_required_ok(monkeypatch):
    """service.set_required -> True -> 204 + flag actualizado con required=True."""
    from controllers.mfa import set_required as mfa_set_required
    from shared.db.models.auth.enums import AuthMfaKind

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.set_required.return_value = True

    monkeypatch.setattr(
        mfa_set_required,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        mfa_set_required,
        'MfaMethodService',
        lambda _c: mfa_svc,
    )
    monkeypatch.setattr(
        mfa_set_required,
        'AuditService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        mfa_set_required,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(data={'kind': 'totp', 'required': True})
    result = mfa_set_required.SetRequired(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    assert result['data'] == {}
    mfa_svc.set_required.assert_called_once_with(
        user_id=user.id,
        kind=AuthMfaKind.TOTP,
        required=True,
    )
