"""AC-6: disable con total_mfa >= 2 -> 204 (deshabilita el metodo).

Given un user con el metodo activo y total_mfa == 2,
When se invoca mfa.disable con uno,
Then deshabilita el metodo y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_disable_with_two(monkeypatch):
    """AC-6: total_mfa == 2 -> 204 + disable."""
    from controllers.mfa import disable
    from shared.db.models.auth.enums import AuthMfaKind

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.has_active_method.return_value = True
    mfa_svc.count_active.return_value = 2

    monkeypatch.setattr(
        disable,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(disable, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(disable, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(disable, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'email_code'})
    result = disable.Disable(event=event).run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    mfa_svc.disable.assert_called_once_with(
        user_id=user.id,
        kind=AuthMfaKind.EMAIL_CODE,
    )
